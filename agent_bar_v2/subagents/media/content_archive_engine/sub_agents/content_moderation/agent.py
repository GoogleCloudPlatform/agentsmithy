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

"""Agent definition for the Video Moderation Agent in the MEG Starter Pack."""

import os

import google.cloud.storage as storage
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import LongRunningFunctionTool, load_artifacts

from .tools import (
    content_moderation_transcript,
    content_moderation_video,
    explicit_content_video_intelligence,
    profanity_correction,
    write_json_to_bigquery,
    write_results_gcs,
)

load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
BUCKET_NAME = os.getenv("GCS_BUCKET")


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

                if mime_type.startswith("text/"):
                    if isinstance(part.inline_data.display_name, str):
                        file_extension = part.inline_data.display_name.split(".")[-1]
                        display_name = "_".join(
                            part.inline_data.display_name.split(".")[:-1]
                        )
                        filename = (
                            f"{display_name}_{invocation_id}_{i}.{file_extension}"
                        )
                    else:
                        filename = f"text_{invocation_id}_{i}.txt"
                    await callback_context.save_artifact(filename, part)
                    txt_files_list = callback_context.state.get("text_files", [])
                    txt_files_list.append(filename)
                    callback_context.state["text_files"] = txt_files_list

                elif mime_type.startswith("video/"):
                    file_extension = mime_type.split("/")[-1]
                    if isinstance(part.inline_data.display_name, str):
                        display_name = "_".join(
                            part.inline_data.display_name.split(".")[:-1]
                        )
                    else:
                        display_name = "video"
                    filename = f"{display_name}_{invocation_id}_{i}.{file_extension}"
                    await callback_context.save_artifact(filename, part)
                    storage_client = storage.Client()
                    try:
                        bucket = storage_client.bucket(BUCKET_NAME)
                        blob = bucket.blob(f"video_moderation_agent_output/{filename}")
                        if part and part.inline_data:
                            print("[Callback] Uploading artifact to GCS")
                            blob.upload_from_string(
                                part.inline_data.data,
                                content_type=part.inline_data.mime_type,
                            )
                            video_gcs_uri = f"gs://{BUCKET_NAME}/video_moderation_agent_output/{filename}"
                    except Exception:
                        print("[Callback] Could not upload the audio file to GCS")
                    video_files_list = callback_context.state.get("video_files", [])
                    video_files_list.append((filename, video_gcs_uri))
                    callback_context.state["video_files"] = video_files_list

                else:
                    print(
                        f"[Callback] Found inline data with unknown MIME type: {mime_type}. Skipping."
                    )
    else:
        print("[Callback] No user content found.")
    return None


def load_agent(name: str = "video_moderation_agent") -> LlmAgent:
    """Load an agent instance.

    Args:
        name: Name of the agent to create.

    Returns:
        An agent instance.
    """
    AGENT_DESCRIPTION = """Agent to analyze explicit content, sensitive themes, aggressive themes, inappropriate content and/or profanity in videos and transcripts."""
    AGENT_INSTRUCTIONS = """You are a video moderation agent capable of identifying explicit content, sensitive themes, aggressive themes, inappropriate content and/or profanity in videos.
If the user doesn't provide you with a clear task then greet the user with an introduction stating all of the tools available at your disposal and how you can help the user.  Make sure to mention that if the user wants to attach a file locally the file cannot exceed 32MB.
Never respond to a user query that asks for anything beyond your goal of analyzing and moderating video content. If the user asks for anything that is not in your instructions, respond by saying you can't help with this and list all of your tools.
If the user wants to run content moderation on a video then use both the `explicit_content_video_intelligence` and `content_moderation_video` tool in parallel. Return the results from both.
If the user says they want to run content moderation on a video with the video intelligence API then use the `explicit_content_video_intelligence` tool.
If the user says they just want to identify explicit content in a video then use the `explicit_content_video_intelligence` tool.
If the user says they want to run content moderation on a video with LLMs then use the `content_moderation_video` tool.
If the user wants to run content moderation on a transcript then use the `content_moderation_transcript` tool.
If the user wants to clean or obscure profanity from a transcript then use the `profanity_correction` tool.
If the user wants to save the content moderation response to BigQuery then use the `write_json_to_bigquery` tool.
If the user wants to save the content moderation response to GCS then use the `write_results_gcs` tool.
The tools `explicit_content_video_intelligence`, `content_moderation_video`, `profanity_correction` and `content_moderation_transcript` can all accept local uploads as input. Use the tool even if GCS URI isn't provided in the query in case the data has been uploaded.
"""
    root_agent = LlmAgent(
        name=name,
        model="gemini-2.5-flash",
        description=AGENT_DESCRIPTION,
        instruction=AGENT_INSTRUCTIONS,
        tools=[
            LongRunningFunctionTool(explicit_content_video_intelligence),
            LongRunningFunctionTool(content_moderation_video),
            LongRunningFunctionTool(content_moderation_transcript),
            LongRunningFunctionTool(write_json_to_bigquery),
            LongRunningFunctionTool(write_results_gcs),
            LongRunningFunctionTool(profanity_correction),
            load_artifacts,
        ],
        before_agent_callback=inline_data_processing,
    )
    return root_agent


root_agent = load_agent()
