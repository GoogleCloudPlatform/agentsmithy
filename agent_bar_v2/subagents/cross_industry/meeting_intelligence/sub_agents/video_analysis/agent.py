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
# limitations under the License."""Agent definition for the Video Analysis Agent in the MEG Starter Pack."""

"""Agent definition for the Video Analysis Agent in the MEG Starter Pack."""


import os

import google.cloud.storage as storage
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import LongRunningFunctionTool, load_artifacts

from .tools import (
    content_categorization,
    entity_analysis,
    scene_analysis,
    shot_analysis,
    storyboard_highlight_reel,
    storyboard_trailer,
    write_json_to_bigquery,
    write_results_gcs,
    write_synopsis,
)

from ...config import PROJECT_ID, LOCATION, BUCKET_NAME


async def inline_data_processing(callback_context: CallbackContext) -> None:
    """
    Processed any inline data files that are provided by the user and sets the state so that the data can be picked by the tools.
    """
    invocation_id = callback_context.invocation_id
    user_content = callback_context.user_content

    if user_content and user_content.parts:
        for i, part in enumerate(user_content.parts):
            if part.inline_data:
                mime_type = part.inline_data.mime_type
                if not mime_type:
                    continue

                if isinstance(part.inline_data.display_name, str):
                    file_extension = part.inline_data.display_name.split(".")[-1]
                    safe_basename = os.path.basename(part.inline_data.display_name)
                    display_name = "_".join(safe_basename.split(".")[:-1])
                    filename = f"{display_name}_{invocation_id}_{i}.{file_extension}"

                if mime_type.startswith("text/"):
                    print("Identified attached text file.")
                    if not filename:
                        filename = f"text_{invocation_id}_{i}.txt"
                    await callback_context.save_artifact(filename, part)
                    print(f"Uploaded text artifact to: {filename}")
                    txt_files_list = callback_context.state.get("text_files", [])
                    txt_files_list.append(filename)
                    callback_context.state["text_files"] = txt_files_list

                elif mime_type.startswith("video/"):
                    if not filename:
                        filename = f"video_{invocation_id}_{i}.{file_extension}"
                    await callback_context.save_artifact(filename, part)
                    print(f"Uploaded video artifact to: {filename}")
                    storage_client = storage.Client()
                    try:
                        bucket = storage_client.bucket(BUCKET_NAME)
                        blob = bucket.blob(
                            f"video_analysis_agent_output/uploads/{filename}"
                        )
                        if part and part.inline_data:
                            blob.upload_from_string(
                                part.inline_data.data,
                                content_type=part.inline_data.mime_type,
                            )
                            video_gcs_uri = f"gs://{BUCKET_NAME}/video_analysis_agent_output/uploads/{filename}"
                            print(f"Uploaded artifact to GCS: {video_gcs_uri}")
                            video_files_list = callback_context.state.get(
                                "video_files", []
                            )
                            video_files_list.append((filename, video_gcs_uri))
                            callback_context.state["video_files"] = video_files_list
                    except Exception as e:
                        print(f"Could not upload the audio file to GCS: {e}")

                else:
                    print(
                        f"Found inline data with unknown MIME type: {mime_type}. Skipping."
                    )
    else:
        print("[Callback] No user content found.")
    return None


def load_agent(name: str = "video_analysis_agent") -> LlmAgent:
    """Load an agent instance.

    Args:
        name: Name of the agent to create.

    Returns:
        An agent instance.
    """

    AGENT_DESCRIPTION = (
        """Agent to analyze scene, shot and entity information from videos."""
    )
    AGENT_INSTRUCTIONS = """You are a video processing agent capable of identifying and analysing scenes, shots and entities.
If the user doesn't provide you with a clear task then greet the user with an introduction stating all of the tools available at your disposal and how you can help the user. Make sure to mention that if the user wants to attach a file locally the file cannot exceed 32MB.
Never respond to a user query that asks for anything beyond your goal of analyzing video content. If the user asks for anything that is not in your instructions or toolset, respond by saying you can't help with this and list all of your tools.
If the user wants to generate information on scenes and scene transitions then use the `scene_analysis` tool.
If the user wants to generate information on shots and shot transitions then use the `shot_analysis` tool.
If the user wants to save tool outputs to BigQuery then use the `write_json_to_bigquery` tool.
If the user wants to further analyze or extract the role of a particular entity (character, location or object) in a video then use the `entity_analysis` tool.
If the user wants to generate a synopsis of the video then use the `write_synopsis` tool. Don't use your own knowledge to generate the synopsis.
If the user wants to generate a trailer or short marketing material for the video use the `storyboard_trailer` tool. If the user hasn't provided scene analysis information or hasn't run the scene analysis tool before then first run the scene analysis tool to generate the input.
If the user wants to generate a highlight reel or marketing video focused on a particular entity then use the `storyboard_highlight_reel` tool. If the user hasn't provided entity analysis information or hasn't run the entity analysis tool before then first run the entity analysis tool to generate the input.
If the user wants to generate tags or metadata for categorizing the content then use the `content_categorization` tool.
"""
    root_agent = LlmAgent(
        name=name,
        model="gemini-2.5-flash",
        description=AGENT_DESCRIPTION,
        instruction=AGENT_INSTRUCTIONS,
        tools=[
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
        ],
        before_agent_callback=inline_data_processing,
    )
    return root_agent


root_agent = load_agent()
