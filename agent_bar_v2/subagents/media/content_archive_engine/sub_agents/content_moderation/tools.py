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

"""Tools for Video Moderation Agent"""

import json
import os
import re
import time
import uuid
from enum import Enum

from dotenv import load_dotenv
from google import genai
from google.adk.tools import ToolContext
from google.cloud import bigquery, storage, videointelligence
from google.cloud.exceptions import GoogleCloudError, NotFound
from google.genai import types
from google.genai.types import Part
from pydantic import BaseModel, Field

from google.adk.tools import LongRunningFunctionTool, load_artifacts

from .config import PROJECT_ID, LOCATION, BUCKET_NAME


async def explicit_content_video_intelligence(
    tool_context: ToolContext,
    video_gcs_uri: str = "",
    artifact_name: str = "",
) -> dict:
    """Use the Video Intelligence API to detect explicit content in videos.
    The video can be a local upload available in the state already or it could be a GCS URI.

    Args:
        video_gcs_uri (str): The GCS URI to the video file being analyzed.
        artifact_name: Path to a local artifact uploaded by the user.
        tool_context (ToolContext): Contains the state, including any uploaded files.
    Returns:
        dict: Dictionary indicating status and in case of success includes the JSON results from the API.
    """
    filenames = tool_context.state.get("video_files")
    if not artifact_name and not video_gcs_uri and filenames:
        # If no input is provided, use last file added to state.
        video_gcs_uri = filenames[-1][1]

    elif artifact_name:
        print("Identified video artifact")
        filenames = tool_context.state.get("video_files")
        if filenames:
            for name, uri in filenames:
                # Find the GCS URI for the video artifact stored in state
                if name == artifact_name:
                    video_gcs_uri = uri
                    break
    if not video_gcs_uri:
        return {
            "status": "error",
            "message": "Please provide the video file you want to run explicit content detection on.",
        }
    try:
        # Use the Video Intelligence API to identify explicit content
        video_client = videointelligence.VideoIntelligenceServiceClient()
        features = [videointelligence.Feature.EXPLICIT_CONTENT_DETECTION]

        operation = video_client.annotate_video(
            request={"features": features, "input_uri": video_gcs_uri}
        )

        result = operation.result(timeout=500)

        output = []
        # Extract the scenes that the Video Intelligence API identified as possibly explicit.
        for frame in result.annotation_results[0].explicit_annotation.frames:
            likelihood = videointelligence.Likelihood(frame.pornography_likelihood).name
            if likelihood in ["POSSIBLE", "LIKELY", "VERY_LIKELY"]:
                frame_time = (
                    frame.time_offset.seconds + frame.time_offset.microseconds / 1e6
                )
                output.append(
                    {"frame_time": frame_time, "pornography_likelihood": likelihood}
                )
        return {"status": "success", "explicit_content_results": json.dumps(output)}
    except Exception:
        return {
            "status": "error",
            "message": "Could not generate shot analysis results due to error. Please make sure that you provided a valid video file that can be processed by the Video Intelligence API.",
        }


class ViolationType(str, Enum):
    """
    Represents possible Violation Type options.
    """

    PROFANITY = "profanity"
    INAPPROPRIATE = "inappropriate_content"
    AGGRESSIVE = "aggressive_themes"
    SENSITIVE = "sensitive_themes"


class Video_Violation(BaseModel):
    """
    Represents a content violation in a video with its type, start and end time,
    content description.
    """

    moderation_violation_type: ViolationType = Field(
        ...,
        description="The type of the content violation detected. Either  `profanity` or `inappropriate_content` or `aggressive_themes` or `sensitive_themes`.",
    )
    start_time: str = Field(
        ...,
        description="The start time of the detected moderation violation in the format HRS:MIN:SEC (e.g., 01:15:30, 00:12:45).",
        pattern="^([0-9]{2}):([0-9]{2}):([0-9]{2})$",
    )
    end_time: str = Field(
        ...,
        description="The end time of the detected content moderation violation in the format HRS:MIN:SEC (e.g., 01:20:45, 00:20:18).",
        pattern="^([0-9]{2}):([0-9]{2}):([0-9]{2})$",
    )
    description: str = Field(
        ...,
        description="A brief description of why the content was flagged and how it fits the type of content moderation violation.",
    )


async def content_moderation_video(
    tool_context: ToolContext,
    video_gcs_uri: str = "",
    artifact_name: str = "",
    gemini_model: str = os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview"),
) -> dict:
    """Use LLMs to conduct content moderation on videos to detect sensitive, inappropriate, explicit and/or aggressive content.
    The video can be a local upload available in the state already or it could be a GCS URI.

    Args:
        video_gcs_uri (str): The GCS URI to the video file being analyzed in the format `gs://bucket-name/path/to/file`.
        gemini_model (str): Gemini model to use for processing.
        tool_context (ToolContext): Contains the state, including any uploaded files.
        artifact_name (str): Path to a local artifact uploaded by the user.
    Returns:
        dict: Dictionary that includes status of error/success.
        If success then includes all violations detected in the video.
    """
    filenames = tool_context.state.get("video_files")
    if not artifact_name and not video_gcs_uri and filenames:
        # If no input is provided, use last file added to state.
        video_gcs_uri = filenames[-1][1]

    elif artifact_name:
        print("Identified video artifact")
        filenames = tool_context.state.get("video_files")
        if filenames:
            for name, uri in filenames:
                # Find the GCS URI for the artifact from the state
                if name == artifact_name:
                    video_gcs_uri = uri
                    break

    if not video_gcs_uri:
        return {
            "status": "error",
            "message": "Provide the GCS URI to the video you want to run your video moderation on or upload the video locally.",
        }

    # Configure the call to Gemini
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    prompt = """Your role is to moderate the video presented before you based only on the Moderation Guidelines listed below:

## Moderation Guidelines:
There are 4 types of guideline violations: `profanity`, `inappropriate_content`, `aggressive_themes` and `sensitive_themes`.

### Profanity: If the video contains an offensive or abusive swear word that is visibly written or mentioned loud and clear, flag the swear word as violation type `profanity`. On the description of the guideline violation, mention the swear word and in the violation timestamp indicate the exact time where this violation happens inside the video.

### Inappropriate Content: If the video contains one of the following:
  - alcohol
  - tobacco or marijuana products
  - firearms and ammunitions
  - prescription drugs
  - illegal drugs and related drug paraphernalia
  - lotteries and gambling
add the violation as violation type `inappropriate_content`. On the description of the violation mention what you found on the video and in the violation timestamp indicate the exact time where this violation happens inside the video. Only tag something as inappropriate content if the video contains something from the specified list. Do not use any other criteria or your own judgment to define inappropriate content.

### Aggressive themes: If the video content falls under any of the following themes:
- Promoting violence
- Promoting hatred in general towards others
- Promoting bullying, inclusive of intimidation, threats, harassment, name-calling, etc.
add the violation as violation type `aggressive_themes`. On the description of the violation mention what you found on the video and in the violation timestamp indicate the exact time where this violation happens inside the video.

### Sensitive themes: If the video contains any of the following themes:
- Current or past political agendas
- Self-harm or suicidal themes
- Providing advice and/or resources that is medical, self-help, psychological, and/or directive in any way.
- Religion
add the violation as violation type `sensitive_themes`. On the description of the violation mention what you found on the video and in the violation timestamp indicate the exact time where this violation happens inside the video.

Identify all of the violations in the video based on the moderation guidelines provided:
"""

    max_number_retries = 2
    retry_time = 2
    retries = 0
    # Generate a response with Gemini
    while retries <= max_number_retries:
        try:
            response = client.models.generate_content(
                model=gemini_model,
                contents=[
                    Part.from_text(text=prompt),
                    Part.from_uri(file_uri=(video_gcs_uri), mime_type="video/mp4"),
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                    top_p=1,
                    max_output_tokens=8000,
                    response_mime_type="application/json",
                    response_schema=list[Video_Violation],
                ),
            )
            if response.text:
                valid_json = json.loads(response.text)
                return {
                    "status": "success",
                    "content_moderation_results": json.dumps(valid_json),
                }
            else:
                raise ValueError("Response can't be None")

        except Exception:
            time.sleep(retry_time)
            retry_time = retry_time * 2
            retries += 1
    return {"status": "error", "message": "Gemini could not generate a valid response."}


class Transcript_Violation(BaseModel):
    """
    Represents a content violation in a transcript with its type, sentence it appears in, content description of the violation.
    """

    moderation_violation_type: ViolationType = Field(
        ...,
        description="The type of the content violation detected. Either  `profanity`, `inappropriate_content`, `aggressive_themes` or `sensitive_themes`.",
    )
    segment: str = Field(
        ...,
        description="The sentence in which the violation is observed.",
    )
    description: str = Field(
        ...,
        description="A brief description of why the content was flagged and how it fits the type of content moderation violation identified.",
    )


async def content_moderation_transcript(
    tool_context: ToolContext,
    transcript_gcs_uri: str = "",
    artifact_name: str = "",
    transcript: str = "",
    gemini_model: str = "gemini-2.5-pro",
) -> dict:
    """Use LLMs to conduct content moderation on transcripts to detect sensitive, inappropriate, explicit and/or aggressive content.
    The video can be a local upload available in the state already, it could be provided as a string or it could be a GCS URI.
    Args:
        transcript_gcs_uri (str): The GCS URI of the transcript for the video file
        transcript (str): The transcript of the video file provided as a string.
        gemini_model (str): Gemini model to use for processing.
        artifact_name (str): Path to a local artifact uploaded by the user.
        tool_context (ToolContext): Contains the state, including any uploaded files.
    Returns:
        dict: Response from the LLM containing all violations found in the transcript.
    """
    found_transcript = False
    if transcript:
        found_transcript = True

    elif transcript_gcs_uri:
        try:
            storage_client = storage.Client()
            path_parts = transcript_gcs_uri[5:].split("/", 1)
            bucket_name = path_parts[0]
            blob_name = path_parts[1]
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            if blob.name.endswith((".txt")):
                transcript = blob.download_as_text()
                found_transcript = True
            else:
                return {
                    "status": "error",
                    "message": "Provide the GCS URI to a valid text file",
                }

        except Exception:
            return {
                "status": "error",
                "message": "Provide the GCS URI to a valid text file.",
            }

    else:
        filenames = tool_context.state.get("text_files")
        if not artifact_name and filenames:
            artifact_name = filenames[-1]
        if artifact_name:
            txt_part = await tool_context.load_artifact(artifact_name)
            if txt_part and txt_part.inline_data and txt_part.inline_data.data:
                transcript = txt_part.inline_data.data.decode("utf-8")
                found_transcript = True

    if not found_transcript:
        return {
            "status": "error",
            "message": "Provide the GCS URI to the transcript or the transcript itself that you want to run profanity cleanup on.",
        }

    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    system_instruction = """
Your role is to moderate a transcript based only on the Moderation Guidelines listed below:

## Moderation Guidelines:
There are 4 types of guideline violations: `profanity`, `inappropriate_content`, `aggressive_themes` and `sensitive_themes`.

### Profanity:
If the transcript contains an offensive or abusive swear word, flag the swear word as violation type `profanity`. In the description of the violation, mention the swear word. Output the sentence where the swear word was detected in the `segment` field of the output.

### Inappropriate Content:
If the transcript contains a mention of one of the following:
  - alcohol
  - tobacco or marijuana products
  - firearms and ammunitions
  - illegal drugs and related drug paraphernalia
  - lotteries and gambling
add the violation as violation type `inappropriate_content`. On the description of the violation mention what you found in the transcript and in the violation segment indicate the exact segment where this violation happens inside the transcript. Only tag something as inappropriate content if the video contains something from the specified list. Do not use any other criteria or your own judgment to define inappropriate content.

### Aggressive themes:
If the transcript content falls under any of the following themes:
- Promoting violence
- Promoting hatred in general towards others
- Promoting bullying, inclusive of intimidation, threats, harassment, name-calling, etc.
add the violation as violation type `aggressive_themes`. On the description of the violation mention what you found in the transcript and in the violation segment indicate the exact segment where this violation happens inside the transcript.

### Sensitive themes:
If the transcript contains any of the following themes:
- Current or past political agendas
- Self-harm or suicidal themes
- Providing advice and/or resources that is medical, self-help, psychological, and/or directive in any way.
- Religion
add the violation as violation type `sensitive_themes`. On the description of the violation mention what you found in the transcript and in the violation segment indicate the exact segment where this violation happens inside the transcript.

Identify all of the violations in the transcript based on the moderation guidelines provided.
"""
    prompt = """Identify all of the content moderation violations in this transcript: {transcript}"""
    prompt_with_data = prompt.format(transcript=transcript)
    max_number_retries = 1
    retry_time = 2
    retries = 0
    # Generate Gemini response
    while retries <= max_number_retries:
        try:
            response = client.models.generate_content(
                model=gemini_model,
                contents=[
                    Part.from_text(text=prompt_with_data),
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0,
                    max_output_tokens=8000,
                    response_mime_type="application/json",
                    response_schema=list[Transcript_Violation],
                ),
            )
            if response.text:
                valid_json = json.loads(response.text)
                return {
                    "status": "success",
                    "explicit_content_results": json.dumps(valid_json),
                }
            else:
                raise ValueError("Response can't be None")
        except Exception:
            time.sleep(retry_time)
            retry_time = retry_time * 2
            retries += 1
    return {
        "status": "error",
        "message": "Gemini could not generate a valid response. ",
    }


async def write_json_to_bigquery(
    json_data: str, table_name: str, dataset_id: str, data_type: str
) -> dict:
    """Writes a list of JSON objects to a BigQuery table. The JSON objects must be generated as a response of `content_moderation_video` or `content_moderation_transcript` or `explicit_content_video_intelligence` tools.

    Args:
        - json_data (str): JSON string returned from a tool.
        - table_name (str): BigQuery table name for the new table.
        - dataset_id (str): BigQuery Dataset ID to which the table will be written.
        - data_type (str): The type of result being written to BigQuery.
        `video_intelligence_explicit_content_response` or `llm_moderation_response_video` or `llm_moderation_response_transcript`

    Returns:
        dict: A dictionary containing the status and a message (success or error).
        The success message contains the dataset and table information
        where the data was written to.
    """
    client = bigquery.Client(project=PROJECT_ID)
    # Set the schema for each type of content
    if data_type == "video_intelligence_explicit_content_response":
        schema = [
            bigquery.SchemaField("frame_time", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("pornography_likelihood", "STRING", mode="REQUIRED"),
        ]
        match = re.search(r"\[.*\]", json_data, re.DOTALL)
    elif data_type == "llm_moderation_response_video":
        schema = [
            bigquery.SchemaField(
                "moderation_violation_type", "STRING", mode="REQUIRED"
            ),
            bigquery.SchemaField("start_time", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("end_time", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("description", "STRING", mode="REQUIRED"),
        ]
        match = re.search(r"\[.*\]", json_data, re.DOTALL)
    elif data_type == "llm_moderation_response_transcript":
        schema = [
            bigquery.SchemaField(
                "moderation_violation_type", "STRING", mode="REQUIRED"
            ),
            bigquery.SchemaField("segment", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("description", "STRING", mode="REQUIRED"),
        ]
        match = re.search(r"\[.*\]", json_data, re.DOTALL)
    else:
        return {
            "status": "error",
            "message": "I can only write LLM Video Moderation, LLM transcript moderation or Explicit Scene Detection results to BQ.",
        }

    try:
        dataset_ref = client.dataset(dataset_id)
        client.get_dataset(dataset_ref)
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        try:
            dataset.location = LOCATION
            client.create_dataset(
                dataset, exists_ok=True
            )  # exists_ok handles concurrent creation
            print(f"Created dataset {client.project}.{dataset.dataset_id}.")
        except GoogleCloudError:
            return {
                "status": "error",
                "message": f"Failed to create dataset '{dataset_id}'.",
            }

    table_ref = client.dataset(dataset_id).table(table_name)
    try:
        client.get_table(table_ref)
    except NotFound:
        table = bigquery.Table(table_ref, schema=schema)
        try:
            table = client.create_table(table)  # API request
            print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
        except GoogleCloudError:
            return {
                "status": "error",
                "message": f"Failed to create table '{table_name}' in dataset '{dataset_id}'.",
            }
    except GoogleCloudError:
        return {"status": "error", "message": f"Failed to access table '{table_name}'."}

    if not match:
        return {
            "status": "error",
            "message": "No JSON array found in the input string.",
        }

    json_string = match.group(0)
    try:
        parsed_json_data = json.loads(json_string)
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON data provided."}

    errors = client.insert_rows_json(table_ref, parsed_json_data)

    if errors:
        return {"status": "error", "message": "Failed to insert rows."}

    return {
        "status": "success",
        "message": f"The information has been written to `{dataset_id}.{table_name}`",
    }


async def write_results_gcs(
    content: str, output_format: str, file_name: str = ""
) -> dict:
    """Write the resulting transcript to GCS.
    Args:
        file_name (str): Name of the file to be written to GCS provided by the user.
        content (str): The text to be written to GCS
        output_format (str): `txt`, `json` formats.
    Returns:
        dict: Dictionary containing status and in case of success the GCS URI to the file written to GCS
    """
    if output_format.lower() not in ["txt", "json"]:
        return {
            "status": "error",
            "message": "Invalid output_format. Must be 'txt' or 'json'.",
        }

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    # Generate a unique filename using UUID
    if not file_name:
        unique_id = uuid.uuid4()
        file_name = f"output_{unique_id}"

    if output_format.lower() == "txt":
        file_extension = ""
        if ".txt" not in file_name:
            file_extension = ".txt"
        gcs_blob_name = f"video_moderation_agent_output/{file_name}{file_extension}"

        # Create a Blob object and upload string directly to GCS
        try:
            blob = bucket.blob(gcs_blob_name)
            blob.upload_from_string(content, content_type="text/plain")

            return {
                "status": "success",
                "gcs_uri": f"gs://{BUCKET_NAME}/{gcs_blob_name}",
            }
        except Exception:
            return {"status": "error", "message": "Could not write JSON string to GCS."}

    else:
        try:
            _ = json.loads(content)
            file_extension = ""
            if ".json" not in file_name:
                file_extension = ".json"
            gcs_blob_name = f"video_moderation_agent_output/{file_name}{file_extension}"

            # Create a Blob object and upload string directly to GCS
            blob = bucket.blob(gcs_blob_name)
            blob.upload_from_string(content, content_type="application/json")
            return {
                "status": "success",
                "gcs_uri": f"gs://{BUCKET_NAME}/{gcs_blob_name}",
            }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid JSON string. Could not write JSON file to GCS because of JSON Decode Error.",
            }
        except Exception:
            return {"status": "error", "message": "Could not write JSON string to GCS."}


async def profanity_correction(
    language: str,
    tool_context: ToolContext,
    transcript_gcs_uri: str = "",
    transcript: str = "",
    artifact_name: str = "",
    gemini_model: str = os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview"),
) -> dict:
    """Use LLMs to identify profanity words in a transcript and obscure the detected words with asterisks.
    The transcript can be a local upload available in the state already, it could be a transcript string or it could be a GCS URI.

    Args:
        language (str): Language of the source transcript.
        transcript_gcs_uri (str): The GCS URI of the transcript for the video file
        transcript (str): The transcript of the video file provided as a string.
        gemini_model (str): Gemini model to use for processing.
        artifact_name (str): Path to a local artifact uploaded by the user.
        tool_context (ToolContext): Contains the state, including any uploaded files.

    Returns:
        dict: Dictionary that includes status of error/success. If success then includes the cleaned transcript.
    """
    found_transcript = False
    if transcript:
        found_transcript = True

    elif transcript_gcs_uri:
        try:
            storage_client = storage.Client()
            path_parts = transcript_gcs_uri[5:].split("/", 1)
            bucket_name = path_parts[0]
            blob_name = path_parts[1]
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            if blob.name.endswith((".txt", ".vtt")):
                transcript = blob.download_as_text()
                found_transcript = True
            else:
                return {
                    "status": "error",
                    "message": "Provide the GCS URI to a valid text file",
                }

        except Exception:
            return {
                "status": "error",
                "message": "Provide the GCS URI to a valid text file.",
            }

    else:
        filenames = tool_context.state.get("text_files")
        if not artifact_name and filenames:
            artifact_name = filenames[-1]
        if artifact_name:
            txt_part = await tool_context.load_artifact(artifact_name)
            if txt_part and txt_part.inline_data and txt_part.inline_data.data:
                transcript = txt_part.inline_data.data.decode("utf-8")
                found_transcript = True

    if not found_transcript:
        return {
            "status": "error",
            "message": "Provide the GCS URI to the transcript or the transcript itself that you want to run profanity cleanup on.",
        }

    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    system_instruction = """### Task
You are a language expert in {language}. Your task is to identify all profane words and phrases in a transcript, and replace them with asterisks. The goal is to obscure profanity while retaining the original word's first letter and length.

### Instructions
1.  **Identify Profanity:** Recognize and find all unequivocally offensive words and phrases.
2.  **Obscure Profanity:** For each profane word, keep the first letter and replace the rest of the characters with an asterisk (`*`).
    * **Example:** "hell" should become "h***".
    * **Example:** "damn it" should become "d*** it".
3.  **Return the Modified Text:** Your final output must be the complete, modified transcript with profanities obscured. Do not output any other explanation.
"""
    prompt = """Clean-up the profanity in this transcript: {transcript}
Output:
"""
    prompt_with_data = prompt.format(transcript=transcript, language=language)
    max_number_retries = 2
    retry_time = 2
    retries = 0
    # Generate gemini response
    while retries <= max_number_retries:
        try:
            response = client.models.generate_content(
                model=gemini_model,
                contents=[
                    Part.from_text(text=prompt_with_data),
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0,
                    top_p=1,
                    max_output_tokens=20000,
                ),
            )
            return {"status": "success", "profanity_removed_transcript": response.text}
        except Exception:
            time.sleep(retry_time)
            retry_time = retry_time * 2
            retries += 1
    return {
        "status": "error",
        "message": "Gemini could not generate a valid response. ",
    }

tools = [
    LongRunningFunctionTool(explicit_content_video_intelligence),
    LongRunningFunctionTool(content_moderation_video),
    LongRunningFunctionTool(content_moderation_transcript),
    LongRunningFunctionTool(write_json_to_bigquery),
    LongRunningFunctionTool(write_results_gcs),
    LongRunningFunctionTool(profanity_correction),
    load_artifacts,
]
