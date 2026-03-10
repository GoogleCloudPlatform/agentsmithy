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

"""Callbacks for the Video Analysis Agent."""

import os
import google.cloud.storage as storage
from google.adk.agents.callback_context import CallbackContext
from .config import BUCKET_NAME

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
