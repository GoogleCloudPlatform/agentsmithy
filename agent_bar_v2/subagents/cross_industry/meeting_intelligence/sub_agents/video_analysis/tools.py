# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tools for Video Analysis Agent"""

import json
import os
import re
import time
import uuid
from typing import Dict, List, Optional, Union

import google.cloud.storage as storage
from google import genai
from google.adk.tools import ToolContext
from google.cloud import bigquery, videointelligence
from google.cloud.exceptions import GoogleCloudError, NotFound
from google.genai import types
from google.genai.types import Part
from pydantic import BaseModel, Field, RootModel

from .config import BUCKET_NAME, LOCATION, PROJECT_ID


def input_processing_helper(
    string_content: Union[str, None],
    gcs_uri: Union[str, None],
    bq_table_id: Union[str, None],
    input_type: str,
) -> tuple[str, str]:
    """For the tools that take input as string, gcs_uri or bq_table_id, reviews the input format and extracts the data.

    Args:
        string_content: String data provided to the tool.
        gcs_uri: GCS URI provided to the tool.
        bq_table_id: bq_table_id provided to the tool.
        type: `entity` or `scene` indicating type of input data being processed

    Returns: A pair where the first element is error/success and the second element is the data in case of success and message in case of error.
    """
    if string_content:
        # Validate the JSON string provided.
        if input_type == "scene":
            match = re.search(r"\[.*?\]", string_content, re.DOTALL)
        else:
            match = re.search(r"\{.*\}", string_content, re.DOTALL)
        if not match:
            return ("error", "Invalid JSON provided as input.")
        json_string = match.group(0)
        return ("success", json_string)

    elif gcs_uri:
        # Validate GCS URI provided
        if not gcs_uri.startswith("gs://") or gcs_uri.count("/") < 3:
            return (
                "error",
                "Invalid GCS URI format. Must be 'gs://bucket-name/path/to/file.json'.",
            )
        path_parts = gcs_uri[5:].split("/", 1)
        bucket_name = path_parts[0]
        blob_name = path_parts[1]
        try:
            gcs_client = storage.Client()
            bucket = gcs_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            if not blob_name.lower().endswith(".json"):
                return ("error", "Invalid file type. The file must be JSON.")
            # Check if the blob exists
            if not blob.exists():
                return ("error", "Invalid GCS URI.")
            json_string = blob.download_as_text()
            return ("success", json_string)
        except Exception:
            return ("error", "Error when reading the file from GCS")
    elif bq_table_id:
        match = re.fullmatch(
            r"([a-z0-9-]+)\.([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)", bq_table_id
        )
        if match:
            project_id, dataset_id, table_id = match.groups()
        else:
            return (
                "error",
                "Invlid GQ Table ID. The Table ID must have format `project_id.dataset_id.table_id`",
            )
        bq_client = bigquery.Client(project=project_id)
        table_ref = bq_client.dataset(dataset_id).table(table_id)

        try:
            bq_client.get_table(table_ref)
        except Exception:
            return (
                "error",
                "Error when getting table information from BQ. Validate that the table exists and you've provided the correct Table ID",
            )

        rows_as_dict = []
        try:
            # Construct a SQL query to select all data
            query = f"SELECT * FROM `{project_id}.{dataset_id}.{table_id}`"
            query_job = bq_client.query(query)
            results = query_job.result()

            # Iterate through the rows and convert each to a dictionary
            for row in results:
                row_dict = dict(row)
                rows_as_dict.append(row_dict)
            json_string = json.dumps(rows_as_dict, indent=2)
            return ("success", json_string)
        except Exception:
            return ("error", "Error when reading data from the BQ table.")
    else:
        return (
            "error",
            "You need to provide scene transition analysis information to be able to generate entity analysis results.",
        )


class Scene(BaseModel):
    """
    Represents a scene in a video with its start and end time, content description and numbering.
    """

    scene_number: int = Field(
        ..., description="The scene number in sequential order, e.g., 1, 2, 3."
    )
    start_time: str = Field(
        ...,
        description="The start time of the scene in the format HRS:MIN:SEC (e.g., 01:15:30, 00:12:45).",
        pattern="^([0-9]{2}):([0-9]{2}):([0-9]{2})$",
    )
    end_time: str = Field(
        ...,
        description="The end time of the scene in the format HRS:MIN:SEC (e.g., 01:20:45, 00:20:18).",
        pattern="^([0-9]{2}):([0-9]{2}):([0-9]{2})$",
    )
    description: str = Field(
        ...,
        description="A brief description of the scene including all important places, characters, events and objects.",
    )


async def scene_analysis(
    tool_context: ToolContext,
    video_gcs_uri: str = "",
    vtt_gcs_uri: str = "",
    artifact_name_vtt: str = "",
    artifact_name_video: str = "",
    gemini_model: str = os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
) -> dict:
    """Use LLMs to do a scene analysis on a video to identify scene transitions
    and if requested generate summaries for each scene.
    Args:
        video_gcs_uri (str): The GCS URI to the video file provided by the user starting with `gs://`.
        vtt_gcs_uri (str): The GCS URI to the .vtt file provided by the user starting with `gs://`.
        artifact_name_vtt (str): Path to a local vtt artifact uploaded by the user.
        artifact_name_video (str): Path to a local video artifact uploaded by the user.
        gemini_model (str): Gemini model to use for processing.
    Returns:
        dict: Dictionary where the keys are indexes for scene numbers
        and the content is (start time, end time, summary)
    """
    vtt_content = None
    filenames = tool_context.state.get("video_files")
    if not artifact_name_video and not video_gcs_uri and filenames:
        # If no input is provided, use last file added to state.
        video_gcs_uri = filenames[-1][1]

    if artifact_name_video:
        print("Identified video artifact")
        filenames = tool_context.state.get("video_files")
        if filenames:
            for name, uri in filenames:
                # Find the GCS URI for the video artifact stored in state
                if name == artifact_name_video:
                    video_gcs_uri = uri
                    break
    if not video_gcs_uri:
        return {
            "status": "error",
            "message": "Please provide the video file you want to run scene analysis on.",
        }

    if artifact_name_vtt:
        print("Identified VTT artifact")
        txt_part = await tool_context.load_artifact(artifact_name_vtt)
        if txt_part and txt_part.inline_data and txt_part.inline_data.data:
            vtt_content = txt_part.inline_data.data.decode("utf-8")

    # Configure GenAI SDK
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    prompt = """
You are a multimodal Scene Boundary Detector.
Your task is to analyze a video {vtt_addition}file to identify cohesive and meaningful scene transitions,
ensuring accurate segmentation into self-contained scenes with distinct narrative arcs.
** Key criteria for identifying scene transitions:**
- Narrative Changes: Transitions must reflect a significant shift in story elements such as location, time, characters, or topic of dialogue.
- Don't treat jump-cuts or insert shots as transitions unless they signify meaningful narrative shifts.
- Visual Cues: Changes in location, character appearance, or recognition of visual elements strongly indicate scene changes.
- Dialogue Topics: Continuous dialogues between a stable set of characters typically belong to a single scene; changes in dialogue themes can signal scene transitions.
- Audio Elements: Shifts in background music or sound effects often accompany scene transitions, reinforcing narrative changes.
- Cohesion: Ensure each identified scene is cohesive, with a contained beginning, middle, and end, contributing to the overarching narrative.
Ensure that the scene transition timestamps you identify strictly fall within the start and end time boundaries of the input video, and accurately reflect the exact position of the scene boundaries in the video.
"""

    max_number_retries = 2
    retry_time = 2
    retries = 0
    # Attempt to generate gemini response with exponential backoff
    while retries <= max_number_retries:
        try:
            if vtt_content:  # If user provided VTT content
                print("Generating scene analysis with vtt content")
                prompt_with_data = prompt.format(
                    vtt_addition="along with its VTT (subtitle) "
                )
                response = client.models.generate_content(
                    model=gemini_model,
                    contents=[
                        Part.from_text(text=prompt_with_data),
                        Part.from_uri(file_uri=(video_gcs_uri), mime_type="video/mp4"),
                        Part.from_text(text=vtt_content),
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0,
                        top_p=1,
                        max_output_tokens=8000,
                        response_mime_type="application/json",
                        response_schema=list[Scene],
                    ),
                )
            elif vtt_gcs_uri:  # If user provided GCS URI to VTT file
                print("Generating scene analysis with vtt URI")
                prompt_with_data = prompt.format(
                    vtt_addition="along with its VTT (subtitle) "
                )
                response = client.models.generate_content(
                    model=gemini_model,
                    contents=[
                        Part.from_text(text=prompt_with_data),
                        Part.from_uri(file_uri=(video_gcs_uri), mime_type="video/mp4"),
                        Part.from_uri(file_uri=(vtt_gcs_uri), mime_type="text/vtt"),
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0,
                        top_p=1,
                        max_output_tokens=8000,
                        response_mime_type="application/json",
                        response_schema=list[Scene],
                    ),
                )
            else:  # If user didn't provide VTT data
                print("Generating scene analysis without vtt content")
                prompt_with_data = prompt.format(vtt_addition="")
                response = client.models.generate_content(
                    model=gemini_model,
                    contents=[
                        Part.from_text(text=prompt_with_data),
                        Part.from_uri(file_uri=video_gcs_uri, mime_type="video/mp4"),
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0,
                        top_p=1,
                        max_output_tokens=8000,
                        response_mime_type="application/json",
                        response_schema=list[Scene],
                    ),
                )
            # Validate that the model returned a valid JSON
            if response.text:
                _ = json.loads(response.text)
                return {
                    "status": "success",
                    "scene_analysis_response": f"{response.text}",
                }
            else:
                raise ValueError("Response can't be None")
        except NotFound:
            return {
                "error": "One of the provided GCS URIs was not found. Please ensure the paths are correct. If you've provided both video and VTT files for the scene analysis make sure either both are local uploads or both are GCS URIs. "
            }
        except Exception:
            time.sleep(retry_time)
            retry_time = retry_time * 2
            retries += 1
    return {
        "status": "error",
        "message": "Gemini could not generate a valid response. ",
    }


class EntitySceneRole(BaseModel):
    """
    Represents the role of an entity within a specific scene.
    """

    scene_number: int = Field(..., description="The sequential number of the scene.")
    start_time: str = Field(
        ..., description="The start timestamp of the scene (HH:MM:SS.ms)."
    )
    end_time: str = Field(
        ..., description="The end timestamp of the scene (HH:MM:SS.ms)."
    )
    role_in_scene: str = Field(
        ...,
        description="A concise summary of the entity's primary role or action in this specific scene.",
    )


class EntityRoleOutput(RootModel[Dict[str, List[EntitySceneRole]]]):
    """
    The top-level output structure for entity roles across scenes.
    The key is the entity's name, and the value is a list of EntitySceneRole objects.
    """


async def entity_analysis(
    entity_name: str,
    scene_analysis_string: str = "",
    gcs_uri: str = "",
    bq_table_id: str = "",
    gemini_model: str = os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
) -> dict:
    """Given scene analysis information containing a list of scenes from a video file
    with summaries of each scene and an entity name, identify each scene the entity is contained in the video.
    The entity can be a character, location or object that might make an appearance in the video.

    Args:
        - entity_name: The name of the entity (character, object or location) searched in the video scenes.
        - scene_analysis_string: The scene analysis JSON information provided as a string.
        - gcs_uri: The GCS URI containing the scene analysis JSON information.
        - bq_table_id: The Big Query table ID `project_id.dataset_id.table_id`
        to the table containing the scene analysis information.
        - gemini_model: Gemini model used for processing.

    Returns:
        dict: Dictionary containing success or error message of the generation.
        The success message must contain the entity analysis information generated.
    """
    status, content = input_processing_helper(
        scene_analysis_string, gcs_uri, bq_table_id, "scene"
    )
    if status == "success":
        json_string = content
    else:
        return {"status": status, "message": content}

    # Configure the call to Gemini
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    prompt = f"""You are an expert in video content analysis. Your task is to extract specific scene information for a given entity (character, location, or object) from a provided JSON string of video scene descriptions.

**Input:**
1.  **Scene Information JSON String:** This will be a string containing a JSON object with a "scene_transition_response" key, which itself contains a "message" key holding a stringified JSON array of scene objects. Each scene object has "scene_number", "start_time", "end_time", and "description".
2.  **Entity Name:** This will be a string representing the entity to search for (e.g., "Lydia Wexler", "main kitchen set", "salmon").

**Instructions:**
1.  **Parse the Scene Information:** Extract the array of scene objects from the "scene_transition_response.message" field within the input JSON string.
2.  **Identify Relevant Scenes:** Go through each scene in the extracted array. Determine if the provided "Entity Name" is present or significantly involved in the "description" of that scene.
3.  **Determine Entity's Role:** For each relevant scene, infer the primary role or action the "Entity Name" plays within that scene. This role should be a concise summary of their contribution or presence.
4.  **Format Output:** Generate a JSON object where the **key is the "Entity Name"**. The value for this key will be a JSON array. Each object in this array represents a scene where the entity appears and must contain the following fields:
    * `scene_number` (integer)
    * `start_time` (string)
    * `end_time` (string)
    * `role_in_scene` (string) - This is the role you determined in step 3.
Entity Name: {entity_name}
Scene Information: {json_string}
"""

    max_number_retries = 2
    retry_time = 2
    retries = 0
    while retries <= max_number_retries:
        try:
            response = client.models.generate_content(
                model=gemini_model,
                contents=[
                    Part.from_text(text=prompt),
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                    top_p=1,
                    max_output_tokens=8000,
                    response_mime_type="application/json",
                    response_schema=EntityRoleOutput,
                ),
            )
            # Verify that Gemini returned a valid JSON.
            if response.text:
                _ = json.loads(response.text)
                return {
                    "status": "success",
                    "entity_analysis_response": f"{response.text}",
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
    table_name: str, dataset_id: str, data_type: str, json_data: str = ""
) -> dict:
    """Writes a list of JSON objects to a BigQuery table. The JSON objects must be generated by the `scene_analysis` or `entity_analysis` or `shot_analysis` or `content_categorization` tools.

    Args:
        json_data (str): JSON string returned from a tool.
        table_name (str): BigQuery table name for the new table.
        dataset_id (str): BigQuery Dataset ID to which the table will be written.
        data_type (str): `scene_analysis` or `entity_analysis` or `shot_analysis` or `content_categorization` indicating
        the type of result being written to BigQuery.

    Returns:
        dict: A dictionary containing the status and a message (success or error).
        The success message contains the dataset and table information where the data was written to.
    """

    client = bigquery.Client(project=PROJECT_ID)
    # Set table schema for each data type
    if data_type == "shot_analysis":
        schema = [
            bigquery.SchemaField("start_time", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("end_time", "FLOAT", mode="REQUIRED"),
        ]
        match = re.search(r"\[.*\]", json_data, re.DOTALL)
    elif data_type == "scene_analysis":
        schema = [
            bigquery.SchemaField("scene_number", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("start_time", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("end_time", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("description", "STRING", mode="REQUIRED"),
        ]
        match = re.search(r"\[.*\]", json_data, re.DOTALL)
    elif data_type == "entity_analysis":
        schema = [
            bigquery.SchemaField(
                "entity_name",
                "STRING",
                mode="REQUIRED",
                description="The name of the character, location, or object.",
            ),
            bigquery.SchemaField(
                "scenes",
                "RECORD",
                mode="REPEATED",  # This makes it an array of records
                description="A list of scenes where the entity appears, with role details.",
                fields=[
                    bigquery.SchemaField(
                        "scene_number",
                        "INTEGER",
                        mode="REQUIRED",
                        description="The sequential number of the scene.",
                    ),
                    bigquery.SchemaField(
                        "start_time",
                        "STRING",
                        mode="REQUIRED",
                        description="The start timestamp of the scene (HH:MM:SS.ms).",
                    ),
                    bigquery.SchemaField(
                        "end_time",
                        "STRING",
                        mode="REQUIRED",
                        description="The end timestamp of the scene (HH:MM:SS.ms).",
                    ),
                    bigquery.SchemaField(
                        "role_in_scene",
                        "STRING",
                        mode="REQUIRED",
                        description="A concise summary of the entity's primary role or action in this specific scene.",
                    ),
                ],
            ),
        ]
        match = re.search(r"\{.*\}", json_data, re.DOTALL)
    elif data_type == "content_categorization":
        schema = [
            bigquery.SchemaField("video_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField(
                "content_tags",
                "RECORD",
                mode="NULLABLE",
                fields=[
                    bigquery.SchemaField("genre", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("subgenres", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("themes", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("mood", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("pacing", "STRING", mode="REPEATED"),
                    bigquery.SchemaField(
                        "setting_and_location", "STRING", mode="REPEATED"
                    ),
                    bigquery.SchemaField("plot_keywords", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("audience", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("visual_style", "STRING", mode="REPEATED"),
                ],
            ),
        ]
        match = re.search(r"\{.*\}", json_data, re.DOTALL)
    else:
        return {
            "status": "error",
            "message": "I can only write scene analysis, shot analysis, content categorization or entity analysis results to BQ.",
        }

    try:
        # Check if dataset exists
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
                "message": f"Failed to create dataset '{dataset_id}'",
            }

    table_ref = client.dataset(dataset_id).table(table_name)
    try:
        # Check if table exists
        client.get_table(table_ref)
    except NotFound:
        table = bigquery.Table(table_ref, schema=schema)
        try:
            table = client.create_table(table)  # API request
            print(f"Created table {table.dataset_id}.{table.table_id}")
        except GoogleCloudError:
            return {
                "status": "error",
                "message": f"Failed to create table '{table_name}' in dataset '{dataset_id}'",
            }
    except GoogleCloudError:
        return {"status": "error", "message": f"Failed to access table '{table_name}'"}

    if not match:
        return {
            "status": "error",
            "message": "No JSON array found in the input string.",
        }

    json_string = match.group(0)
    try:
        parsed_json_data = json.loads(json_string)
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON data provided"}

    # Insert data to BigQuery
    if data_type in ["scene_analysis", "shot_analysis"]:
        errors = client.insert_rows_json(table_ref, parsed_json_data)

    elif data_type == "entity_analysis":
        rows_to_insert = []
        for entity_name, scenes_list in parsed_json_data.items():
            row = {"entity_name": entity_name, "scenes": scenes_list}
            rows_to_insert.append(row)
        errors = client.insert_rows_json(table_ref, rows_to_insert)

    else:
        rows_to_insert = []
        for video_name, tags_list in parsed_json_data.items():
            row = {"video_name": video_name, "content_tags": tags_list[0]}
            rows_to_insert.append(row)
        errors = client.insert_rows_json(table_ref, rows_to_insert)

    if errors:
        return {"status": "error", "message": f"Failed to insert rows: {errors}"}
    return {
        "status": "success",
        "message": f"The information has been written to `{PROJECT_ID}.{dataset_id}.{table_name}`",
    }


async def write_results_gcs(content: str, file_name: str) -> dict:
    """Write the resulting JSON from the various tools to GCS.
    Args:
        file_name (str): Name of the file to be written to GCS provided by the user.
        content (str): The text to be written to GCS
    Returns:
        dict: Dictionary indicating status and in case of success returns GCS URI of the file.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    # Generate a unique filename using UUID
    if not file_name:
        unique_id = uuid.uuid4()
        file_name = f"output_{unique_id}"

    try:
        _ = json.loads(content)
        file_extension = ""
        if ".json" not in file_name:
            file_extension = ".json"
        gcs_blob_name = f"video_analysis_agent_output/{file_name}{file_extension}"

        # Create a Blob object and upload string directly to GCS
        blob = bucket.blob(gcs_blob_name)
        blob.upload_from_string(content, content_type="application/json")

        return {"status": "success", "gcs_uri": f"gs://{BUCKET_NAME}/{gcs_blob_name}"}
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "Invalid JSON string. Could not write JSON file to GCS because of JSON Decode Error.",
        }
    except Exception:
        return {"status": "error", "message": "Failed to write to GCS"}


async def write_synopsis(
    scene_analysis: str = "",
    bq_table_id: str = "",
    gemini_model: str = os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
) -> dict:
    """Use LLMs to generate synopsis for videos from their scene analysis results.
    The scene analysis info can be provided as strings or a BQ table ID.

    Args:
        bq_table_id (str): The Big Query table ID to the table containing scene information.
        scene_analysis (str): The scene analysis information for the video.
        gemini_model (str): Gemini model to use for processing.

    Returns:
        dict: Dictionary to indicate success/error message. If success includes the synopsis generated.
    """
    status, content = input_processing_helper(
        scene_analysis, None, bq_table_id, "scene"
    )
    if status == "success":
        scene_analysis = content
    else:
        return {"status": status, "message": content}

    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    prompt = """You are an expert in content marketing. Given the scene analysis information to a media file containing descriptions of each scene, generate a 2-4 sentences long synopsis for the video.
The synopsis has to give a short overview of what is happening in the video.
The language should be engaging and should inspire all types of customers to watch the video without giving away the ending.
Transcript: {scene_analysis}
Synopsis:"""

    prompt_with_data = prompt.format(scene_analysis=scene_analysis)

    max_number_retries = 2
    retry_time = 2
    retries = 0
    # Attempt to generate gemini response with exponential backoff
    while retries <= max_number_retries:
        try:
            response = client.models.generate_content(
                model=gemini_model,
                contents=[
                    prompt_with_data,
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                ),
            )
            return {"status": "success", "synopsis_results": response.text}
        except Exception:
            time.sleep(retry_time)
            retry_time = retry_time * 2
            retries += 1
    return {"status": "error", "message": "Gemini could not generate synopsis."}


async def shot_analysis(
    tool_context: ToolContext,
    video_gcs_uri: str = "",
    artifact_name: str = "",
) -> dict:
    """Use the Video Intelligence API to do a shot analysis on a video to detect shot changes.
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

    if artifact_name:
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
            "message": "Provide the GCS URI to the video you want to run your scene analysis on or upload the video locally.",
        }

    video_client = videointelligence.VideoIntelligenceServiceClient()
    features = [videointelligence.Feature.SHOT_CHANGE_DETECTION]
    try:
        operation = video_client.annotate_video(
            request={"features": features, "input_uri": video_gcs_uri}
        )
        result = operation.result(timeout=600)
        parsed_json_data = []
        for shot in result.annotation_results[0].shot_annotations:
            start_time = (
                shot.start_time_offset.seconds
                + shot.start_time_offset.microseconds / 1e6
            )
            end_time = (
                shot.end_time_offset.seconds + shot.end_time_offset.microseconds / 1e6
            )

            parsed_json_data.append({"start_time": start_time, "end_time": end_time})
        return {
            "status": "success",
            "shot_analysis_results": json.dumps(parsed_json_data),
        }
    except Exception:
        return {
            "status": "error",
            "message": "Could not generate shot analysis results due to error. Please make sure that you provided a valid video file that can be processed by the Video Intelligence API.",
        }


async def storyboard_trailer(
    duration: int = 90,
    scene_analysis: str = "",
    bq_table_id: str = "",
    gemini_model: str = os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
) -> dict:
    """Use LLMs to generate storyboards for trailers from the scene analysis results of videos.
    The scene analysis info can be provided as strings or a BQ table ID.

    Args:
        duration (int): How long you want the video to be in seconds
        bq_table_id (str): The Big Query table ID to the table containing scene information.
        scene_analysis (str): The scene analysis information for the video.
        gemini_model (str): Gemini model to use for processing.

    Returns:
        dict: Includes status of the tool. If success includes the storyboard of the trailer.
    """
    status, content = input_processing_helper(
        scene_analysis, None, bq_table_id, "scene"
    )
    if status == "success":
        scene_analysis = content
    else:
        return {"status": status, "message": content}

    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    prompt = """### Persona and Task
You are a professional film trailer editor and storyteller. Your task is to analyze a detailed scene-by-scene breakdown of a show or film and create a compelling, {duration}-second trailer storyboard. A good trailer should be fast-paced, create a sense of mystery and excitement, and tell a mini-narrative that hooks the audience without giving away the ending.

### Storyboard Structure and Requirements
Your output must be a play-by-play of the trailer. For each shot, you must specify the following:

1.  **Trailer Timestamp:** The cumulative timestamp of the trailer itself (e.g., `00:00 - 00:05`). The total length should be approximately {duration} seconds.
2.  **Original Scene and Timestamps:** The specific scene number and the exact start and end timestamps from the provided input (e.g., `Scene 1, from 00:00:00 to 00:05:00`).
3.  **Visual Description:** A concise, vivid description of the on-screen action, focusing on what a viewer would see.
4.  **Audio Description:** The accompanying audio, including music, sound effects, and dialogue.

### Trailer Arc Plan
Follow this flexible narrative structure for the trailer, adapting the pacing and tone based on the provided scene content.

* **Hook:** Start with a quick, engaging montage of shots to grab attention. Use a variety of short clips from the content to establish the premise and tone.
* **Setup / Introduction:** Introduce the main character(s) and the initial situation. Build a sense of anticipation and the core conflict or premise.
* **Rising Tension / The Central Challenge:** This is the core of the trailer. Show the dramatic turning point or reveal of the central challenge. Use shots that highlight character reactions and the introduction of a major obstacle or opponent.
* **Climax / Stakes:** A high-energy montage of key moments. Mix quick cuts of action, intense close-ups of characters, emotional reactions, and flashes of the rewards or consequences. As needed use a voiceover to quickly explain the rules or stakes.
* **Final Cut:** End with a single, powerful shot—either an emotional peak, a compelling piece of dialogue, or an intense action shot—followed by a quick blackout and a tagline.

### Input: Scene Analysis
Below is the scene-by-scene breakdown of the content, including timestamps and descriptions. Use this information as your sole source of truth for the trailer's content:

{scene_analysis}

### Final Output Format
Present the storyboard as a clear, easy-to-read list, following the guidelines provided:
"""

    prompt_with_data = prompt.format(scene_analysis=scene_analysis, duration=duration)
    max_number_retries = 2
    retry_time = 2
    retries = 0
    # attempt to generate gemini response with exponential backoff
    while retries <= max_number_retries:
        try:
            response = client.models.generate_content(
                model=gemini_model,
                contents=[
                    prompt_with_data,
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                ),
            )
            return {"status": "success", "storyboard_trailer_results": response.text}
        except Exception:
            time.sleep(retry_time)
            retry_time = retry_time * 2
            retries += 1
    return {
        "status": "error",
        "synopsis_results": "Gemini could not generate a response.",
    }


async def storyboard_highlight_reel(
    entity_name: str,
    duration: int = 90,
    entity_analysis: str = "",
    bq_table_id: str = "",
    gemini_model: str = os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
) -> dict:
    """Use LLMs to generate storyboards for highlight reels focusing on a particular entity
    in a video based on entity analysis input provided.
    The entity analysis info can be provided as strings or a BQ table ID.

    Args:
        - entity_name (str): What entity you want the highlight reel to focus on. An entity could be a character, item or location.
        - duration (int): How long you want the video to be in seconds
        - bq_table_id (str): The Big Query table ID to the table containing entity information.
        - entity_analysis (str): The entity analysis information for the video.
        - gemini_model (str): Gemini model to use for processing.

    Returns:
        dict: Dictionary that includes status of error/success. If success then includes the storyboard of the highlight reel focused on the entity.
    """
    if not entity_name:
        return {
            "status": "error",
            "message": "You need to provide an entity name for the highlight reel indicating what the content should be focused on.",
        }

    status, content = input_processing_helper(
        entity_analysis, None, bq_table_id, "entity"
    )
    if status == "success":
        entity_analysis = content
    else:
        return {"status": status, "message": content}

    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    prompt = """### Persona and Task
You are a professional film content editor, specializing in creating character-centric and entity-focused promotional content. Your task is to analyze a detailed scene-by-scene breakdown of a show or film and create a compelling, {duration}-second trailer storyboard. This trailer must focus exclusively on one key entity: {target_entity} and build a mini-narrative that generates excitement and intrigue about their journey.

### Storyboard Structure and Requirements
Your output must be a play-by-play of the trailer. For each shot, you must specify the following:

1.  **Highlight Reel Timestamp:** The cumulative timestamp of the trailer itself (e.g., `00:00 - 00:05`). The total length should be approximately {duration} seconds.
2.  **Original Scene and Timestamps:** The specific scene number and the exact start and end timestamps from the provided input (e.g., `Scene 1, from 00:00:00 to 00:05:00`).
3.  **Visual Description:** A concise, vivid description of the on-screen action, focusing on what a viewer would see, specifically highlighting the target entity.
4.  **Audio Description:** The accompanying audio, including music, sound effects, and relevant dialogue from or about the target entity.

### Highlight Reel Arc Plan
Follow this specific narrative structure for the trailer, focusing on the story of the `{target_entity}`.

* **Hook (0-15%):** Start with quick, compelling shots of the `{target_entity}` in various moments of action, emotion, or mystery. The goal is to establish their presence and importance right away.
* **Setup / Introduction (15-40%):** Introduce the `{target_entity}` more clearly, showing their initial situation, personality, or role. Hint at a challenge they will face or a central mystery surrounding them.
* **Rising Tension / The Challenge (40-60%):** This is the core of the trailer. Showcase the conflicts, obstacles, or opposing forces the `{target_entity}` will encounter.
* **Climax / Stakes (60-80%):** A high-energy montage. Mix quick cuts of the `{target_entity}` in key moments of action, emotional breakthroughs, or confrontations. This section should raise the stakes and make the viewer question what will happen to them.
* **Final Cut (80-100%):** End with a powerful, single shot of the `{target_entity}` that leaves a lasting impression, followed by a blackout.

### Input: Scene Analysis and Target Entity
Below is the scene-by-scene breakdown of the content, including timestamps and descriptions. Use this information as your sole source of truth for the trailer's content.

{entity_analysis}

**Target Entity:** {target_entity}

### Final Output Format
Present the storyboard as a clear, easy-to-read list, based on the provided guidelines:
"""

    prompt_with_data = prompt.format(
        entity_analysis=entity_analysis, duration=duration, target_entity=entity_name
    )

    max_number_retries = 2
    retry_time = 2
    retries = 0
    # attempt to generate gemini response with exponential backoff
    while retries <= max_number_retries:
        try:
            response = client.models.generate_content(
                model=gemini_model,
                contents=[
                    prompt_with_data,
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                ),
            )
            return {"status": "success", "storyboard_highlight_results": response.text}
        except Exception:
            time.sleep(retry_time)
            retry_time = retry_time * 2
            retries += 1
    return {"status": "error", "message": "Gemini could not generate results."}


class Tags(BaseModel):
    """
    A comprehensive set of tags for video content categorization.
    """

    genre: Optional[List[str]] = Field(
        default_factory=list, description="Primary and secondary genres of the content."
    )
    subgenres: Optional[List[str]] = Field(
        default_factory=list,
        description="More specific subgenres that provide additional detail.",
    )
    themes: Optional[List[str]] = Field(
        default_factory=list,
        description="Central ideas, motifs, or subjects explored in the content.",
    )
    mood: Optional[List[str]] = Field(
        default_factory=list,
        description="The emotional tone and feeling of the content.",
    )
    pacing: Optional[List[str]] = Field(
        default_factory=list, description="The speed at which the plot develops."
    )
    setting_and_location: Optional[List[str]] = Field(
        default_factory=list,
        description="The time period and physical locations where the story takes place.",
    )
    plot_keywords: Optional[List[str]] = Field(
        default_factory=list,
        description="Concise phrases that describe major plot points or concepts.",
    )
    audience: Optional[List[str]] = Field(
        default_factory=list,
        description="The target demographic based on age, interests, and themes.",
    )
    visual_style: Optional[List[str]] = Field(
        default_factory=list,
        description="Descriptive tags for the cinematography, editing, and overall aesthetic.",
    )


class VideoTagSchema(BaseModel):
    """
    Pydantic schema for video content tagging.
    """

    title: str = Field(..., description="The title of the content.")
    tags: Tags


async def content_categorization(
    tool_context: ToolContext,
    artifact_name: str = "",
    content_title: str = "",
    scene_analysis_bq_table_id: str = "",
    video_gcs_uri: str = "",
    scene_analysis: str = "",
    gemini_model: str = os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
) -> dict:
    """Use LLMs to generate content tags for a video file for categorization and recommendation purposes.
    Generate tags based on the video file or based on the scene analysis generated from the video.

    Args:
        - content_title (str): Name of the content
        - scene_analysis_bq_table_id (str): BigQuery table ID for the scene analysis of the video.
        - video_gcs_uri (str): GCS URI for the video file
        - scene_analysis (str): Scene analysis as a string
        - gemini_model (str): Gemini model to use for processing.
        - artifact_name: Path to a local artifact uploaded by the user.

    Returns:
        dict: Dictionary containing status and if success then contains the tags assigned to the video.
    """
    data_found = False
    if video_gcs_uri or scene_analysis or scene_analysis_bq_table_id:
        data_found = True
    filenames = tool_context.state.get("video_files")
    if not data_found:
        if not artifact_name and filenames:
            # If no input is provided, use last file added to state.
            video_gcs_uri = filenames[-1][1]
            data_found = True

        elif artifact_name:
            filenames = tool_context.state.get("video_files")
            if filenames:
                for name, uri in filenames:
                    # Find the GCS URI for the video artifact stored in state
                    if name == artifact_name:
                        video_gcs_uri = uri
                        data_found = True
                        break

    if not data_found:
        return {
            "status": "error",
            "message": "Provide the scene information or the video to be able to generate content categorization",
        }

    if scene_analysis_bq_table_id:
        match = re.fullmatch(
            r"([a-z0-9-]+)\.([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)",
            scene_analysis_bq_table_id,
        )
        if match:
            project_id, dataset_id, table_id = match.groups()
        else:
            return {
                "status": "error",
                "message": "Invlid BQ Table ID. The Table ID must have format `project_id.dataset_id.table_id`",
            }
        if not content_title:
            content_title = table_id
        bq_client = bigquery.Client(project=PROJECT_ID)
        table_ref = bq_client.dataset(dataset_id).table(table_id)

        try:
            bq_client.get_table(table_ref)
        except Exception:
            return {
                "status": "error",
                "message": "Error when getting table information from BQ. Validate that the table exists and you've provided the correct Table ID",
            }

        rows_as_dict = []
        try:
            # Construct a SQL query to select all data
            query = f"SELECT * FROM `{project_id}.{dataset_id}.{table_id}`"
            query_job = bq_client.query(query)  # API request

            # Wait for the query to complete and get the results
            results = query_job.result()

            # Iterate through the rows and convert each to a dictionary
            # `row` objects behave like dictionaries where you can access fields by name
            for row in results:
                row_dict = dict(row)
                rows_as_dict.append(row_dict)

            scene_analysis = json.dumps(rows_as_dict, indent=2)
        except Exception:
            return {
                "status": "error",
                "message": "Error when reading data from the BQ table",
            }
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    prompt = """You are an expert in multimedia content tagging. Analyze the provided video file or a text file containing a scene-by-scene breakdown. Your task is to tag and categorize the content with as much detail and nuance as possible. The goal is to produce a comprehensive set of metadata that would be valuable for a modern streaming service's recommendation engine and search functions.
Return your analysis in a structured JSON format. For each category, provide 0-5 relevant tags. If a category doesn't apply, omit it from the final JSON.

### Core Categories & Tags

Here are the key categories and the types of tags to include. Go beyond the obvious and use your understanding of the content to find specific, granular tags that match the video.

* **Genre**: The primary and secondary genres of the content. (e.g., Action-Adventure, Romantic Comedy, Psychological Thriller, Sci-Fi)
* **Subgenres**: More specific genres that provide additional detail. (e.g., Heist Film, Courtroom Drama, Supernatural Horror, Teen Sitcom)
* **Themes**: The central ideas, motifs, or subjects explored in the content. (e.g., Coming-of-Age, Revenge, Dystopian Society, Found Family, Underdog Story)
* **Mood**: The emotional tone and feeling of the content. (e.g., Uplifting, Suspenseful, Gritty, Whimsical, Heartbreaking)
* **Pacing**: The speed at which the plot develops. (e.g., Fast-Paced, Slow Burn, Action-Packed, Episodic)
* **Setting & Location**: The time period and physical locations where the story takes place. (e.g., 1980s, Post-Apocalyptic, Urban, Small Town, Space)
* **Plot Keywords**: Concise phrases that describe major plot points, objects, or concepts. (e.g., Time Travel, Magical Powers, Murder Mystery, Bank Robbery, Love Triangle)
* **Audience**: The target demographic based on age, interests, and themes. (e.g., Family-Friendly, Young Adult, Mature Audience, Niche-Interest)

### Video Information:

"""
    max_number_retries = 2
    retry_time = 2
    retries = 0
    # attempt to generate gemini response with exponential backoff
    while retries <= max_number_retries:
        try:
            if video_gcs_uri:
                response = client.models.generate_content(
                    model=gemini_model,
                    contents=[
                        Part.from_text(text=prompt),
                        Part.from_uri(file_uri=video_gcs_uri, mime_type="video/mp4"),
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0,
                        response_mime_type="application/json",
                        response_schema=Tags,
                    ),
                )
                if not content_title:
                    content_title = video_gcs_uri.split("/")[-1]
            else:
                prompt = prompt + scene_analysis
                response = client.models.generate_content(
                    model=gemini_model,
                    contents=[
                        prompt,
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0,
                        response_mime_type="application/json",
                        response_schema=Tags,
                    ),
                )
            if not content_title:
                content_title = str(uuid.uuid4())
            if response.text:
                valid_json = json.loads(response.text)
                complete_response = {content_title: [valid_json]}
                return {
                    "status": "success",
                    "categorization_results": json.dumps(complete_response),
                }
            else:
                raise ValueError("Response can't be None")
        except Exception:
            time.sleep(retry_time)
            retry_time = retry_time * 2
            retries += 1
    return {
        "status": "error",
        "message": "Gemini could not generate content categorization tags.",
    }


from google.adk.tools import LongRunningFunctionTool, load_artifacts

tools = [
    LongRunningFunctionTool(scene_analysis),
    LongRunningFunctionTool(write_json_to_bigquery),
    LongRunningFunctionTool(entity_analysis),
    LongRunningFunctionTool(write_results_gcs),
    LongRunningFunctionTool(shot_analysis),
    LongRunningFunctionTool(write_synopsis),
    LongRunningFunctionTool(storyboard_trailer),
    LongRunningFunctionTool(storyboard_highlight_reel),
    LongRunningFunctionTool(content_categorization),
    load_artifacts,
]
