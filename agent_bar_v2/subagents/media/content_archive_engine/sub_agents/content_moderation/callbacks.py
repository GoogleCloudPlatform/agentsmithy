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
