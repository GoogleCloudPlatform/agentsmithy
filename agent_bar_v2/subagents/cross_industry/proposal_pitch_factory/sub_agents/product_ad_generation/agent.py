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
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext

from .config import BUCKET_NAME, LOCATION, PROJECT_ID
from .prompt import SYSTEM_INSTRUCTIONS
from .tools import (
    generate_and_display_images,
    generate_music_from_prompt,
    produce_final_video_with_sound,
    save_script_to_state,
)



async def inline_data_processing(callback_context: CallbackContext) -> None:
    """
    Processes uploaded files, uploads original images to GCS, and saves the
    GCS path to the agent's state.
    """
    invocation_id = callback_context.invocation_id
    user_content = callback_context.user_content
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    if user_content and user_content.parts:
        for i, part in enumerate(user_content.parts):
            if part.inline_data:
                mime_type = part.inline_data.mime_type
                if not mime_type:
                    continue

                if mime_type.startswith("image/"):
                    if isinstance(part.inline_data.display_name, str):
                        display_name = "_".join(part.inline_data.display_name.split(".")[:-1])
                    else:
                        display_name = "image"

                    filename = f"{display_name}_{invocation_id}_{i}.png"

                    # Save artifact for logs
                    await callback_context.save_artifact(filename, part)

                    # Upload original image to GCS
                    image_gcs_uri = None
                    try:
                        blob = bucket.blob(f"ad_agent_inputs/{filename}")
                        print(f"[Callback] Uploading ORIGINAL {filename} to GCS")
                        # Use the original image data directly
                        blob.upload_from_string(
                            part.inline_data.data,
                            content_type=mime_type,
                        )
                        image_gcs_uri = f"gs://{BUCKET_NAME}/ad_agent_inputs/{filename}"
                        print(f"[Callback] Image GCS URI: {image_gcs_uri}")
                    except Exception as e:
                        print(f"[Callback] Could not upload the image file to GCS: {e}")

                    # Save the GCS path to the agent's state
                    if image_gcs_uri:
                        callback_context.state["image_gcs_uri"] = image_gcs_uri
                        callback_context.state["image_mime_type"] = mime_type

                else:
                    print(f"[Callback] Found inline data with unhandled MIME type: {mime_type}. Skipping.")
    else:
        print("[Callback] No user content or parts found.")
    return None


def load_agent() -> LlmAgent:
    """Load the Product ad generation agent."""

    agent = LlmAgent(
        name="product_ad_generation",
        model="gemini-2.5-flash",
        description=(
            "You are a Product Ad Generation Agent, a helpful AI agent and creative partner that generates multi-scene video advertisements."
            " Your process is interactive and split into precise steps."
        ),
        instruction=SYSTEM_INSTRUCTIONS,
        tools=[
            # NEW Tool for Act 1:
            save_script_to_state,
            # NEW Tool for Act 2:
            generate_and_display_images,
            # NEW Tool for Act 3:
            generate_music_from_prompt,
            # NEW Tool for Act 4:
            produce_final_video_with_sound,
        ],
        before_agent_callback=inline_data_processing,
    )

    return agent


root_agent = load_agent()
