import datetime
import os
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
# from google.adk.apps import App
import google.auth
import google.cloud.storage as storage

from .config import BUCKET_NAME, LOCATION, PROJECT_ID
from .prompt import PRODUCT_AD_AGENT_INSTRUCTIONS
from .tools import (
    generate_and_display_images,
    generate_music_from_prompt,
    produce_final_video_with_sound,
    save_script_to_state,
)

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


if not PROJECT_ID or not LOCATION or not BUCKET_NAME:
    raise EnvironmentError(
        "Missing required environment variables (GOOGLE_CLOUD_PROJECT, "
        "GOOGLE_CLOUD_LOCATION, GCS_BUCKET) in your .env file."
    )

print(f"Loaded config: Project={PROJECT_ID}, Location={LOCATION}, Bucket={BUCKET_NAME}")


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
                        display_name = "_".join(
                            part.inline_data.display_name.split(".")[:-1]
                        )
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
                    print(
                        f"[Callback] Found inline data with unhandled MIME type: {mime_type}. Skipping."
                    )
    else:
        print("[Callback] No user content or parts found.")
    return None


root_agent = Agent(
        name="product_ad_agent",
        model="gemini-2.5-flash",
        description=(
            "You are a Product Ad Generation Agent, a helpful AI agent and "
            "creative partner that generates multi-scene video advertisements. "
            "Your process is interactive and split into precise steps."
        ),
        instruction=PRODUCT_AD_AGENT_INSTRUCTIONS,
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
