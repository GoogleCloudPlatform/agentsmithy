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

import json
import os
from typing import Any, Optional
import logging

import sqlparse
from google.cloud import bigquery
from langchain_community.graphs.graph_document import (
    GraphDocument,
    Node,
    Relationship,
)
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_spanner import SpannerGraphStore, SpannerGraphQAChain, SpannerGraphStore
from langchain_google_vertexai import VertexAIEmbeddings


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# dynamic graph tools
def get_bq_dataset_schema(project_id: str, dataset_id: str) -> str:
    """
    Inspects all tables in a BigQuery dataset and returns their schemas,
    including PRIMARY KEY and FOREIGN KEY constraints, as a JSON string.
    """
    try:
        client = bigquery.Client(project=project_id)

        # 1. Fetch raw table columns
        tables = client.list_tables(f"{project_id}.{dataset_id}")
        schema_info = {}
        for table_item in tables:
            table = client.get_table(table_item)
            schema_info[table.table_id] = {
                "columns": [f"{f.name} ({f.field_type})" for f in table.schema],
                "primary_keys": [],
                "foreign_keys": [],
            }

        # 2. Fetch constraints (PKs and FKs)
        query = f"""
        SELECT
            tc.table_name,
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name,
            ccu.table_name AS referenced_table_name,
            ccu.column_name AS referenced_column_name
        FROM
            `{project_id}.{dataset_id}.INFORMATION_SCHEMA.TABLE_CONSTRAINTS` tc
        LEFT JOIN
            `{project_id}.{dataset_id}.INFORMATION_SCHEMA.KEY_COLUMN_USAGE` kcu
            ON tc.constraint_name = kcu.constraint_name
        LEFT JOIN
            `{project_id}.{dataset_id}.INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE` ccu
            ON tc.constraint_name = ccu.constraint_name
        WHERE
            tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY')
        """
        try:
            results = client.query(query).result()
            for row in results:
                table_name = row["table_name"]
                if table_name not in schema_info:
                    continue

                if row["constraint_type"] == "PRIMARY KEY":
                    if (
                        row["column_name"]
                        and row["column_name"]
                        not in schema_info[table_name]["primary_keys"]
                    ):
                        schema_info[table_name]["primary_keys"].append(
                            row["column_name"]
                        )
                elif row["constraint_type"] == "FOREIGN KEY":
                    fk_entry = {
                        "column": row["column_name"],
                        "referenced_table": row["referenced_table_name"],
                        "referenced_column": row["referenced_column_name"],
                    }
                    if fk_entry not in schema_info[table_name]["foreign_keys"]:
                        schema_info[table_name]["foreign_keys"].append(fk_entry)
        except Exception as query_e:
            logging.warning(f"Could not fetch constraints: {query_e}")

        return json.dumps(schema_info, indent=2) if schema_info else "No tables found."
    except Exception as e:
        return f"Error inspecting BigQuery dataset: {e}"


def is_safe_bq_query(query: str) -> bool:
    """Validates that the query is a single, read-only SELECT statement."""
    parsed = sqlparse.parse(query)

    try:
        # If the query is empty/invalid, parsed will be empty,
        # and parsed[0] will raise an IndexError.
        statement = parsed[0]

        # Deny multi-statement queries and non-SELECT queries
        if len(parsed) > 1 or statement.get_type() != "SELECT":
            return False

        return True

    except IndexError:
        # If we get an IndexError, it's an invalid query, so we fail safely.
        return False


def execute_dynamic_graph_build(
    project_id: str,
    graph_store: SpannerGraphStore,
    build_plan_json: str,
    embedding_service: VertexAIEmbeddings,  # Add embedding_service as an argument
    cleanup_first: bool = False,
) -> str:
    """
    Executes the graph build process, now including explicit embedding generation.
    """
    logging.info("TOOL: Executing Dynamic Graph Build")
    try:
        plan = json.loads(build_plan_json)

        bq_query = plan["bq_etl_query"]
        if not is_safe_bq_query(bq_query):
            logging.error(f"Generated BigQuery query failed validation: {bq_query}")
            return (
                "Error: Malicious or invalid BigQuery query detected. Execution halted."
            )

        client = bigquery.Client(project=project_id)

        rows = list(client.query(plan["bq_etl_query"]).result())
        if not rows:
            return "ETL query returned no results. Graph is empty."

        nodes = {}
        final_relationships = []
        seen_relationships = set()

        for row in rows:
            row_nodes = {
                cfg["node_type"]: nodes.setdefault(
                    (str(row[cfg["id_column"]]), cfg["node_type"]),
                    Node(
                        id=str(row[cfg["id_column"]]),
                        type=cfg["node_type"],
                        properties={
                            "name": str(row[cfg["id_column"]]),
                            "description": f"A graph node representing a {cfg['node_type']} with the name {str(row[cfg['id_column']])}.",
                        },
                    ),
                )
                for cfg in plan["nodes"]
            }
            for rel in plan["relationships"]:
                source = row_nodes.get(rel["source"])
                target = row_nodes.get(rel["target"])
                if source and target:
                    rel_type = rel.get("type", "RELATED_TO")

                    # Now it's safe to access .id and create the key
                    relationship_key = (source.id, target.id, rel_type)

                    if relationship_key not in seen_relationships:
                        seen_relationships.add(relationship_key)
                        final_relationships.append(
                            Relationship(source=source, target=target, type=rel_type)
                        )

        graph_doc = GraphDocument(
            nodes=list(nodes.values()),
            relationships=final_relationships,
            source=Document(page_content="Dynamic Build"),
        )

        # ** NEW STEP: Explicitly generate and attach embeddings to each node **
        logging.info(f"Generating embeddings for {len(graph_doc.nodes)} nodes...")
        for node in graph_doc.nodes:
            node_content_for_embedding = node.properties.get("name", node.id)
            node.properties["embedding"] = embedding_service.embed_query(
                node_content_for_embedding
            )

        if cleanup_first:
            graph_store.cleanup()

        logging.info("Storing graph and embeddings in Spanner...")
        graph_store.add_graph_documents([graph_doc])

        return f"Success! Built graph with {len(nodes)} nodes and {len(final_relationships)} relationships."

    except Exception as e:
        return f"An unexpected error occurred during graph build: {e}"
    
# spanner tools

_qa_chain: Optional[SpannerGraphQAChain] = None

def get_spanner_graph_qa_chain(graph_store: SpannerGraphStore) -> SpannerGraphQAChain:
    """Initializes or returns the cached SpannerGraphQAChain."""
    global _qa_chain
    if _qa_chain:
        return _qa_chain

    # Initialize LLM
    llm = ChatVertexAI(
        model_name="gemini-2.5-flash",
        temperature=0,
        project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        location=os.environ.get("GOOGLE_CLOUD_LOCATION"),
    )

    # Initialize Chain
    _qa_chain = SpannerGraphQAChain.from_llm(
        llm,
        graph=graph_store,
        allow_dangerous_requests=True,
        verbose=True,
        return_intermediate_steps=True,
    )
    return _qa_chain


def get_spanner_schema_core(graph_store: SpannerGraphStore) -> str:
    """
    Retrieves the schema of the Spanner Graph, including node labels and properties.
    Use this to understand what data maps to which properties (e.g. is it 'Active' or 'active'?).
    """
    try:
        chain = get_spanner_graph_qa_chain(graph_store)
        if hasattr(chain.graph, "get_schema"):
            return chain.graph.get_schema
        # Fallback if get_schema property/method access differs
        return str(chain.graph.schema)
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"


def query_spanner_graph_core(question: str, graph_store: SpannerGraphStore) -> str:
    """
    Answers a question by querying the Spanner Graph.
    Returns the answer and the GQL query used.
    """
    try:
        chain = get_spanner_graph_qa_chain(graph_store)
        result = chain.invoke({"query": question})

        answer = result.get("result", "")
        intermediate_steps = result.get("intermediate_steps", [])

        gql_query = "N/A"
        formatted_result = {
            "answer": answer,
            "generated_gql": gql_query,
            "intermediate_steps": str(intermediate_steps),
        }

        for step in intermediate_steps:
            if isinstance(step, dict) and "query" in step:
                formatted_result["generated_gql"] = step["query"]
            elif isinstance(step, str) and "GRAPH" in step:
                formatted_result["generated_gql"] = step

        if not answer or answer.strip() == "[]":
            formatted_result["warning"] = (
                "The query returned no results. Consider checking the schema with `get_spanner_schema` or adjusting filters (e.g. case sensitivity)."
            )

        return json.dumps(formatted_result, indent=2)

    except Exception as e:
        return f"Error querying Spanner Graph: {str(e)}"

# agent definitions
def generate_build_plan_tool(
    user_request: str,
    schema_json: str,
    project_id: str,
    dataset_id: str,
    graph_name: str,
) -> Any:
    """
    Generates a detailed JSON build plan, including traversal tools with correct openCypher queries for Spanner Graph.
    """
    print("--- TOOL: Invoking Builder LLM to generate plan ---")
    # Use an f-string to dynamically insert the graph_name into the prompt examples
    builder_prompt = f"""
You are an expert graph data engineer for Spanner Graph. Your task is to generate a 'build plan' JSON object. This plan MUST include four keys:
1. `bq_etl_query`: A BigQuery SQL query to select columns for building the graph.
2. `nodes`: A list of objects defining each node with its `node_type` (label) and `id_column`.
3. `relationships`: A list of objects defining links. Each object MUST have three keys: 'source', 'target', and 'type'. The values for 'source' and 'target' MUST be the string values of the 'node_type' from the nodes list (e.g., "Server", "Employee"). They cannot be dictionaries. The 'type' MUST be an uppercase, snake_case string.
   **IMPORTANT**: If the DATABASE SCHEMA contains `foreign_keys`, you MUST automatically create relationships where the table with the foreign key is the 'source' and the `referenced_table` is the 'target'. You should assign a logical 'type' to these relationships (e.g. "HAS_ACCOUNT", "BELONGS_TO").
4. `traversal_tools`: A dictionary of complete, executable **openCypher** queries to traverse the graph relationships.

   --- CRITICAL SPANNER CYPHER RULES ---
   1.  Every query MUST begin with the 'GRAPH {graph_name}' directive followed by a space.
   2.  Query parameters MUST be prefixed with '@' (e.g., @app_id).
   3.  The relationship label in the MATCH clause is the full edge name constructed by joining the source type, relationship type, and target type with underscores.
   4.  Filter nodes using an explicit `WHERE` clause.
   5.  Self-Consistency Rule: When generating the `traversal_tools`, you MUST use the exact relationship `type` values you defined in the `relationships` section above to construct the edge labels.

   **Example of a correct query for a relationship defined as `source: "App", target: "Repo", type: "HAS_REPO"`:**
   The constructed edge label is `App_HAS_REPO_Repo`.
   The correct query for `get_repos_for_app` is:
   `GRAPH {graph_name} MATCH (a:App)-[:App_HAS_REPO_Repo]->(r:Repo) WHERE a.id = @app_id RETURN r.id AS id`

Your output MUST be ONLY the raw JSON object, without any markdown fences, comments, or other text.
"""
    # The context now explicitly includes the graph_name for the LLM
    context_string = f"CONTEXT:\nProject ID: {project_id}\nDataset ID: {dataset_id}\nGraph Name: {graph_name}\n\nDATABASE SCHEMA:\n{schema_json}"

    # Use the .invoke() method with a list of LangChain message objects
    response = ChatVertexAI(model="gemini-2.5-flash").invoke(
        [
            SystemMessage(content=f"{builder_prompt}\n\n{context_string}"),
            HumanMessage(content=user_request),
        ]
    )
    return response.content


def summarize_build_plan_tool(build_plan_json: str) -> Any:
    """
    Takes a raw JSON build plan and returns a human-readable summary.
    """
    print("--- TOOL: Invoking Summarizer LLM to generate summary ---")
    summarizer_prompt = (
        "You are a helpful project manager. Your task is to take a technical JSON build plan and describe it to a non-technical user. "
        "Do not show any code, SQL, or Cypher. Your output MUST have two sections:"
        "1. 'Graph Structure': Describe the entities (nodes) and the relationships between them in simple terms. Show the relationship flow (e.g., App -> Repo -> Table)."
        "2. 'Available Tools': List each tool from the 'traversal_tools' section. For each tool, provide a simple, one-sentence description of what it does (e.g., 'Given an App, this tool finds its code Repositories.')."
        "Your entire output must be in markdown."
    )
    response = ChatVertexAI(model="gemini-2.5-flash", temperature=0).invoke(
        f"{summarizer_prompt}\n\nJSON PLAN:\n{build_plan_json}"
    )
    return response.content
