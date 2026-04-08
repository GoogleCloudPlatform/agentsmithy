# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import traceback
from urllib.parse import urlparse
import yaml
from dotenv import load_dotenv
from google.adk.tools import FunctionTool
from google.api_core.exceptions import GoogleAPIError
from google.cloud import bigquery, bigquery_migration_v2, storage
from vertexai.generative_models import GenerativeModel

load_dotenv()

ANALYZE_SQL_PROMPT = """
The following SQL code has been translated from Oracle to Google BigQuery.
The translation process introduced some placeholder functions and potential BigQuery incompatibility issues.
Your task is to:

1.  **Identify specific errors or incompatible constructs** from the Oracle to BigQuery translation. 
    Pay close attention to the following common issues:
    * `ERROR_UNIMPLEMENTED`: These are direct placeholders for Oracle features that were not automatically translated to BigQuery.
    * For array-clearing, BigQuery typically re-initializes an array to an empty one.
    * `ERROR_COMPILEFAILED`: These often indicate a failure in translating Oracle's sql.
    * In BigQuery, oracles `MEMBER OF` clause for checking array membership is usually replaced with `value IN UNNEST(array_variable)` or `EXISTS(SELECT 1 FROM UNNEST(array_variable) WHERE element = 'value')`.
    * `bqutil.fn.cw_regexp_substr_4`: This is very likely a custom or internal UDF that needs replacement with standard BigQuery functions like `REGEXP_EXTRACT` or `SPLIT` followed by `UNNEST` for string parsing.
    * `DUAL` table: BigQuery does not use a `DUAL` table like Oracle. Simple single-row selections can often be done directly without a `FROM` clause or by using `FROM UNNEST([1])`.
    * `@@error.message`: BigQuery handles error messages within `EXCEPTION WHEN ERROR` blocks, but the specific syntax for accessing the error message might need confirmation (`@@error.message` is not a standard BigQuery system variable). It typically is available directly within the `EXCEPTION WHEN ERROR` block.
    * Oracle-specific date/time functions or string manipulations that might not be idiomatic BigQuery or could be simplified.
    * `CROSS JOIN` without an explicit `ON` clause: While sometimes valid, it's worth checking if these were intended to be `INNER JOIN`s with implicit conditions from Oracle.
    * `parse_datetime('%Y-%m-%d', V_DATE_VAR) <= datetime_trunc(current_datetime(), DAY)`: Confirm date formatting and function usage.
    * `LET` is specific keyword in oracle . there is no such keyword in bigquery replace it with needed eqvuivalent in bigquery
    * while create parent procedure or actual procedure add `OPTIONS(strict_mode=false)`

2.  For each identified issue, provide a **clear and concise explanation** of why it's an error or incompatible in BigQuery.

3.  Structure your response as a Markdown-formatted list of issues, with each issue having:
    * A clear heading for the issue.
    * **Explanation:** short reason for the incompatibility/error and how it can be fixed in bigquery keep it short.

Here is the SQL code to analyze:
```sql
{sql_content}
```
"""

def run_sql_translationapi(gcs_input_path, gcs_output_path, project_id, location="us"):
    """
    Submits a batch SQL translation job to Google Cloud BigQuery Migration Service.
    """
    print(f"DEBUG: run_sql_translationapi called with:")
    print(f"  gcs_input_path: {gcs_input_path}")
    print(f"  gcs_output_path: {gcs_output_path}")
    print(f"  project_id: {project_id}")
    print(f"  location: {location}")

    client = bigquery_migration_v2.MigrationServiceClient()
    parent = f"projects/{project_id}/locations/{location}"

    translation_config = bigquery_migration_v2.TranslationConfigDetails(
        gcs_source_path=gcs_input_path,
        gcs_target_path=gcs_output_path,
        source_dialect=bigquery_migration_v2.Dialect(
            oracle_dialect=bigquery_migration_v2.OracleDialect()
        ),
        target_dialect=bigquery_migration_v2.Dialect(
            bigquery_dialect=bigquery_migration_v2.BigQueryDialect()
        ),
    )

    task = bigquery_migration_v2.MigrationTask(
        type_="Translation_Oracle2BQ",
        translation_config_details=translation_config,
    )

    workflow = bigquery_migration_v2.MigrationWorkflow(
        display_name="sql-translation-workflow",
    )
    workflow.tasks = {"translation-task": task}

    request = bigquery_migration_v2.CreateMigrationWorkflowRequest(
        parent=parent,
        migration_workflow=workflow,
    )

    response = client.create_migration_workflow(request=request)
    print(f"DEBUG: Migration workflow created successfully. Response name: {response.name}")
    return f"Translation job created: {response.name}"

def parse_gcs_uri_and_find_errors(gcs_output_path):
    """
    Parses a GCS URI (e.g., 'gs://bucket/path/') and identifies error files (*.err.json or *.sql.errors.json) in that directory.
    Returns a list of GCS URIs for the found error files.
    """
    try:
        parsed_uri = urlparse(gcs_output_path)
        if parsed_uri.scheme != 'gs':
            return "Error: Invalid GCS path. Must start with 'gs://'"
        
        bucket_name = parsed_uri.netloc
        prefix = parsed_uri.path.lstrip('/')
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
        
        error_files = []
        for blob in blobs:
            if blob.name.endswith('.err.json') or blob.name.endswith('.sql.errors.json'):
                error_files.append(f"gs://{bucket_name}/{blob.name}")
        
        if not error_files:
            return "No error files found in the specified path."
        return error_files
    except Exception as e:
        return f"Error scanning GCS: {str(e)}"

def analyze_sql_with_gemini(sql_content, model_name="gemini-2.5-flash"):
    """
    Sends translated BigQuery SQL to Gemini for an initial check for 'ERROR_UNIMPLEMENTED' and other known translation artifacts.
    """
    try:
        model = GenerativeModel(model_name)
        prompt = ANALYZE_SQL_PROMPT.format(sql_content=sql_content)
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error calling Gemini for analysis: {str(e)}"

def resolve_sql_error_with_gemini(
    sql_content,
    project_id,
    current_error_message=None,
    initial_analysis=None,
    model_name="gemini-2.5-flash"
):
    """
    Iteratively refines SQL using Gemini to resolve BQ specific translation errors.
    """
    RESOLVE_SQL_BASE_PROMPT = """
    You are an expert BigQuery SQL translator and debugger. Your goal is to fix SQL queries that have BigQuery syntax or compilation errors.
    """

    RESOLVE_SQL_INITIAL_ANALYSIS_PROMPT = """
    I have already performed an initial analysis of this SQL code. Here is a summary of identified issues and suggested fixes from that analysis:

    {initial_analysis}

    Please use this analysis as a primary guide to perform targeted corrections.
    """

    RESOLVE_SQL_ERROR_PROMPT = """
    I have attempted to run the previous version of this SQL query in BigQuery, and it failed the dry run with the following error message:

    ```
    {current_error_message}
    ```

    Please analyze the provided SQL query and this *specific* error message. Your primary goal for this iteration is to resolve the error indicated by the BigQuery compiler.
    """

    RESOLVE_SQL_INSTRUCTION_PROMPT = """
    **CRITICAL INSTRUCTION: Your response MUST contain the COMPLETE AND ENTIRE SQL query.** DO NOT OMIT, SHORTEN, OR TRUNCATE ANY PART of the query. The output must be ready to be copied and executed in BigQuery.

    Current SQL to review and fix:
    ```sql
    {current_sql_content}
    ```

    Provide ONLY the corrected BigQuery SQL query in a markdown code block (```sql...```). Ensure the code block is correctly formed and contains the entire, complete SQL code.
    """

    try:
        model = GenerativeModel(model_name)
        full_prompt = RESOLVE_SQL_BASE_PROMPT
        
        if initial_analysis:
            full_prompt += RESOLVE_SQL_INITIAL_ANALYSIS_PROMPT.format(initial_analysis=initial_analysis)
            
        if current_error_message:
            full_prompt += RESOLVE_SQL_ERROR_PROMPT.format(current_error_message=current_error_message)
            
        full_prompt += RESOLVE_SQL_INSTRUCTION_PROMPT.format(current_sql_content=sql_content)
        
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error calling Gemini for resolution: {str(e)}"

def upload_to_gcs(bucket_name, destination_blob_name, source_content, content_type='text/plain'):
    """Uploads a string content to a GCS bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(source_content, content_type=content_type)
        return f"Content uploaded to gs://{bucket_name}/{destination_blob_name}"
    except Exception as e:
        return f"Error uploading to GCS: {str(e)}"

def generate_bigquery_mapping_yaml(
    source_db,
    source_schema,
    target_project,
    target_dataset
):
    """
    Generates a YAML string for BigQuery translation name mapping.
    """
    mapping = {
        'name_mapping': [
            {
                'source': {
                    'database': source_db,
                    'schema': source_schema
                },
                'target': {
                    'project': target_project,
                    'dataset': target_dataset
                }
            }
        ]
    }
    return yaml.dump(mapping)

# Wrap python function as function tool
mapping_tool = FunctionTool(generate_bigquery_mapping_yaml)
upload_to_gcs_tool = FunctionTool(upload_to_gcs)
run_sql_translation_tool = FunctionTool(run_sql_translationapi)
check_error_files_tool = FunctionTool(parse_gcs_uri_and_find_errors)
analyze_sql_with_gemini_tool = FunctionTool(analyze_sql_with_gemini)
resolve_sql_error_tool = FunctionTool(resolve_sql_error_with_gemini)
