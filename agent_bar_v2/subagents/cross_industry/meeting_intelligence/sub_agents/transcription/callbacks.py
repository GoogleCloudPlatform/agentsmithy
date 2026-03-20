# Copyright 2026 Google LLC. All Rights Reserved.
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

"""Callbacks for the Transcription Agent."""

import os
from google.adk.agents.callback_context import CallbackContext

async def inline_data_processing(callback_context: CallbackContext) -> None:
    """
    Processed any inline data files that are provided by the user and sets the state so that the data can be picked by the tools.
    """
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    user_content = callback_context.user_content

    print(f"\\n[Callback] Entering agent: {agent_name} (Inv: {invocation_id})")

    if user_content and user_content.parts:
        for i, part in enumerate(user_content.parts):
            if part.inline_data:
                mime_type = part.inline_data.mime_type
                if not mime_type:
                    continue
                print(mime_type)
                if mime_type.startswith("text/") and isinstance(
                    part.inline_data.data, str
                ):
                    if isinstance(part.inline_data.display_name, str):
                        file_extension = part.inline_data.display_name.split(".")[-1]
                        safe_basename = os.path.basename(part.inline_data.display_name)
                        display_name = "_".join(safe_basename.split(".")[:-1])
                        filename = (
                            f"{display_name}_{invocation_id}_{i}.{file_extension}"
                        )
                    else:
                        filename = f"image_{invocation_id}_{i}.txt"
                    await callback_context.save_artifact(filename, part)
                    print(f"Uploaded text artifact to: {filename}")
                    txt_files_list = callback_context.state.get("text_files", [])
                    txt_files_list.append(filename)
                    callback_context.state["text_files"] = txt_files_list
                    print(f"Set text files in the state variable to: {filename}")

                elif mime_type.startswith("video/"):
                    file_extension = mime_type.split("/")[-1]
                    if isinstance(part.inline_data.display_name, str):
                        safe_basename = os.path.basename(part.inline_data.display_name)
                        display_name = "_".join(safe_basename.split(".")[:-1])
                    else:
                        display_name = "audio"
                    filename = f"{display_name}_{invocation_id}_{i}.{file_extension}"
                    await callback_context.save_artifact(filename, part)
                    print(f"uploaded video artifact to: {filename}")
                    video_files_list = callback_context.state.get("video_files", [])
                    video_files_list.append(filename)
                    callback_context.state["video_files"] = video_files_list
                    print(f"set video file in the state variable to: {filename}")

                elif mime_type.startswith("audio/"):
                    # Upload the multimedia data to GCS
                    file_extension = mime_type.split("/")[-1]
                    if isinstance(part.inline_data.display_name, str):
                        safe_basename = os.path.basename(part.inline_data.display_name)
                        display_name = "_".join(safe_basename.split(".")[:-1])
                    else:
                        display_name = "audio"
                    filename = f"{display_name}_{invocation_id}_{i}.{file_extension}"
                    await callback_context.save_artifact(filename, part)
                    print(f"uploaded audio artifact to: {filename}")
                    audio_files_list = callback_context.state.get("audio_files", [])
                    audio_files_list.append(filename)
                    callback_context.state["audio_files"] = audio_files_list
                    print(f"set audio file in the state variable to: {filename}")

                else:
                    print(
                        f"Found inline data with unknown MIME type: {mime_type}. Skipping."
                    )
    else:
        print("[Callback] No user content found.")
    return None
