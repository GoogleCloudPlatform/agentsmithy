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

"""
Tools for the Creative AdBot agent.

This file contains all the functions (tools) that the agent can call to perform
its tasks, such as generating images, animating videos, and combining clips.
"""

import base64
import io
import os
import subprocess
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import google.auth
import google.auth.transport.requests
import requests

# --- Google & Vertex AI Imports ---
import vertexai
from google import genai

# --- ADK & Utility Imports ---
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types
from PIL import Image

from .config import AUDIO_GENERATION_MODEL_VERSION, BUCKET_NAME, LOCATION, PROJECT_ID

# ==============================================================================
# --- 0. GCS HELPERS (replaced gsutil) ---
# ==============================================================================


def _parse_gs_uri(uri: str) -> Tuple[str, str]:
    """
    Parse a GCS URI like 'gs://bucket/path/to/blob.ext' -> ('bucket', 'path/to/blob.ext')
    """
    if not uri.startswith("gs://"):
        raise ValueError(f"Not a valid GCS URI: {uri}")
    no_scheme = uri[5:]  # strip 'gs://'
    first_slash = no_scheme.find("/")
    if first_slash == -1:
        # Bucket only, no object path
        return no_scheme, ""
    return no_scheme[:first_slash], no_scheme[first_slash + 1 :]


def _ensure_parent_dir(path: str):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _gcs_download_to_file(
    gcs_uri: str, local_filename: str, storage_client: Optional[storage.Client] = None
):
    client = storage_client or storage.Client()
    bucket_name, blob_path = _parse_gs_uri(gcs_uri)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    _ensure_parent_dir(local_filename)
    # If a stale/readonly file exists, try removing it first
    if os.path.exists(local_filename):
        try:
            os.chmod(local_filename, 0o666)
            os.remove(local_filename)
        except Exception:
            pass
    blob.download_to_filename(local_filename)
    try:
        os.chmod(local_filename, 0o644)
    except Exception:
        pass


def _gcs_upload_from_file(
    gcs_uri: str,
    local_filename: str,
    content_type: Optional[str] = None,
    storage_client: Optional[storage.Client] = None,
):
    client = storage_client or storage.Client()
    bucket_name, blob_path = _parse_gs_uri(gcs_uri)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    if content_type:
        blob.content_type = content_type
    blob.upload_from_filename(local_filename)


def _gcs_move(
    src_gcs_uri: str, dst_gcs_uri: str, storage_client: Optional[storage.Client] = None
):
    """
    Move (copy then delete) an object within/between buckets.
    """
    client = storage_client or storage.Client()
    src_bucket_name, src_blob_path = _parse_gs_uri(src_gcs_uri)
    dst_bucket_name, dst_blob_path = _parse_gs_uri(dst_gcs_uri)

    src_bucket = client.bucket(src_bucket_name)
    dst_bucket = client.bucket(dst_bucket_name)
    src_blob = src_bucket.blob(src_blob_path)

    # Copy
    dst_blob = src_bucket.copy_blob(src_blob, dst_bucket, new_name=dst_blob_path)
    # Delete source
    src_blob.delete()
    return f"gs://{dst_blob.bucket.name}/{dst_blob.name}"


# ==============================================================================
# --- 0.5. WORK DIR (Cloud Run: only /tmp is writable) ---
# ==============================================================================


def _work_dir() -> str:
    """
    Returns a writable working directory. On Cloud Run, /tmp is writable.
    You can override by setting ADK_WORKDIR env var.
    """
    base = os.environ.get("ADK_WORKDIR", "/tmp/adbot")
    os.makedirs(base, exist_ok=True)
    return base


# ==============================================================================
# --- 1. GLOBAL CONFIGURATION & INITIALIZATION ---
# ==============================================================================

# Initialize Vertex AI SDK
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
except Exception as e:
    print(f"Warning: Failed to initialize Vertex AI. {e}")

# Initialize Global Clients
try:
    global_genai_client = genai.Client(
        vertexai=True, project=PROJECT_ID, location=LOCATION
    )
except Exception as e:
    print(f"Warning: Failed to initialize GenAI Client. {e}")
    global_genai_client = None

GLOBAL_VIDEO_MODEL = "veo-2.0-generate-001"

# ==============================================================================
# --- 2. PUBLIC ADK TOOLS (Called by the agent in prompt.py) ---
# ==============================================================================


async def save_script_to_state(
    scene1_prompt: str,
    scene2_prompt: str,
    scene3_prompt: str,
    scene4_prompt: str,
    tool_context: ToolContext,
):
    """
    Saves the four brainstormed scene prompts into the agent's state memory.
    This tool is called after the creative brainstorming step (Act 1).
    """
    try:
        print("Saving script to state...")
        script = [scene1_prompt, scene2_prompt, scene3_prompt, scene4_prompt]
        tool_context.state["creative_script"] = script
        return {"status": "success", "message": "Script saved to state."}
    except Exception as e:
        return {"status": "error", "message": f"Error in save_script_to_state: {e}" }


async def generate_and_display_images(
    tool_context: ToolContext,
) -> List[Dict[str, Any]]:
    """
    Reads the 'creative_script' from state, generates one image for each prompt,
    saves them to GCS, and displays all 4 images as artifacts in the chat.
    This is the main tool for Act 2.
    """
    try:
        print("Generating and displaying images from script in state...")

        if not global_genai_client:
            return [{"status": "error", "message": "GenAI Client not initialized."}]

        # 1. Get the script from state
        script = tool_context.state.get("creative_script", [])
        if not script:
            return [
                {
                    "status": "error",
                    "message": "Could not find script in state. Please start over.",
                }
            ]

        storyboard_data = []  # This is what we will save back to the state
        image_model = "imagen-3.0-generate-002"
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)

        # 2. Loop through the prompts and generate/save/display
        for i, prompt in enumerate(script):
            scene_num = i + 1
            print(f"Generating image for Scene {scene_num}: {prompt}")

            image_response = global_genai_client.models.generate_images(
                model=image_model,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                    person_generation=types.PersonGeneration.ALLOW_ALL,
                ),
            )

            if (
                not image_response.generated_images
                or not image_response.generated_images[0].image
            ):
                print(
                    f"ERROR: Image generation failed or returned invalid data for prompt: {prompt}"
                )
                continue

            pil_img = image_response.generated_images[0].image._pil_image
            if not pil_img:
                print(f"ERROR: Could not decode image data for prompt: {prompt}")
                continue

            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            buf.seek(0)
            verified_img = Image.open(buf)

            final_buf = io.BytesIO()
            verified_img.save(final_buf, format="PNG")
            image_bytes = final_buf.getvalue()

            # 3. Upload to GCS (for the final video tool)
            gcs_file_name = f"scene_{uuid.uuid4()}.png"
            blob = bucket.blob(f"ad_agent_scenes/{gcs_file_name}")
            blob.upload_from_string(image_bytes, content_type="image/png")
            gcs_path = f"gs://{BUCKET_NAME}/ad_agent_scenes/{gcs_file_name}"

            # 4. Save and Display Artifact
            artifact_name = f"storyboard_scene_{scene_num}.png"
            try:
                artifact_part = types.Part.from_bytes(
                    data=image_bytes, mime_type="image/png"
                )
                await tool_context.save_artifact(artifact_name, artifact_part)
                print(f"Saved Scene {scene_num} as artifact: {artifact_name}")

                await tool_context.load_artifact(artifact_name)
                print(f"Loaded artifact {artifact_name} for display.")
            except Exception as e:
                print(f"Error saving/loading artifact {artifact_name}: {e}")

            # 5. Prepare data for the new state
            storyboard_data.append(
                {
                    "scene_prompt": prompt,
                    "image_gcs": gcs_path,
                    "mime_type": "image/png",
                    "artifact_name": artifact_name,
                }
            )

        # 6. Save the FULL storyboard data to a new state variable
        tool_context.state["storyboard_images"] = storyboard_data
        return storyboard_data
    except Exception as e:
        return [{"status": "error", "message": f"Error in generate_and_display_images: {e}" }]


# ==============================================================================
# --- 3. VIDEO PIPELINE (animate & combine) ---
# ==============================================================================


async def _produce_silent_video(output_filename: str, tool_context: ToolContext) -> str:
    """
    (Internal Helper) Reads storyboard from state, animates scenes, and combines
    them into a single SILENT video LOCALLY.

    Returns:
        The LOCAL path to the compiled silent video.
    """
    storyboard = tool_context.state.get("storyboard_images", [])
    if not storyboard:
        return "ERROR: No approved storyboard found in state. Cannot produce video."

    # Ensure we write into a Cloud Run–safe dir
    work = _work_dir()
    # If the caller passed a bare filename, put it under /tmp/adbot
    if not os.path.isabs(output_filename):
        output_path = os.path.join(work, output_filename)
    else:
        output_path = output_filename

    print(
        f"Producing SILENT video from {len(storyboard)} scenes. Output path: {output_path}"
    )
    video_clips_gcs_paths: List[str] = []

    # --- Animate each scene ---
    for i, scene in enumerate(storyboard):
        image_gcs = scene["image_gcs"]
        image_mime = scene["mime_type"]
        clip_name = f"clip_{uuid.uuid4()}.mp4"
        anim_prompt = f"Animation for scene {i + 1}"
        gcs_video_path = generate_video_from_image(
            prompt=anim_prompt,
            image_gcs_uri=image_gcs,
            image_mime_type=image_mime,
            output_name=clip_name,
            duration_seconds=8,
        )
        if "ERROR" in str(gcs_video_path):
            return f"ERROR: Failed during animation of scene {i + 1}."
        video_clips_gcs_paths.append(gcs_video_path)

    # --- Combine clips (FFmpeg logic) ---
    local_files: List[str] = []
    clip_durations: List[float] = []
    concat_list_filename = os.path.join(work, "concat_list.txt")

    storage_client = storage.Client()

    for i, path in enumerate(video_clips_gcs_paths):
        local_name = os.path.join(work, f"local_clip_{i}_{uuid.uuid4()}.mp4")
        _gcs_download_to_file(path, local_name, storage_client)
        local_files.append(local_name)

        # Probe duration
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                local_name,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        clip_durations.append(float(result.stdout.strip()))

    with open(concat_list_filename, "w") as f:
        for file in local_files:
            f.write(f"file '{file}'\n")

    input_args = [arg for file in local_files for arg in ["-i", file]]
    filter_complex = ""
    last_video_stream = "[0:v]"
    current_offset = 0.0
    transition_duration = 1

    for i in range(1, len(local_files)):
        transition_offset = current_offset + clip_durations[i - 1] - transition_duration
        video_stream_name = f"[v{i}]"
        filter_complex += (
            f"{last_video_stream}[{i}:v]xfade=transition=fade:"
            f"duration={transition_duration}:offset={transition_offset}"
            f"{video_stream_name}; "
        )
        last_video_stream = video_stream_name
        current_offset = transition_offset

    filter_complex += f"{last_video_stream}format=yuv420p[final_v]"
    command = [
        "ffmpeg",
        *input_args,
        "-filter_complex",
        filter_complex,
        "-map",
        "[final_v]",
        output_path,
        "-y",
    ]

    try:
        # 3. Create the final SILENT video locally (in /tmp/adbot)
        subprocess.run(command, check=True)
        print(f"Combined silent video saved locally to {output_path}")
        return output_path

    except Exception as e:
        print(f"Error producing silent video: {e}")
        return f"ERROR: Failed during silent video production: {e}"
    finally:
        # Clean up the downloaded clips, but NOT the final silent video
        print("Cleaning up temporary clip files...")
        for file in local_files:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception:
                pass
        try:
            if os.path.exists(concat_list_filename):
                os.remove(concat_list_filename)
        except Exception:
            pass


# ==============================================================================
# --- 3. INTERNAL HELPER TOOLS (Called by other tools) ---
# ==============================================================================


def generate_video_from_image(
    prompt: str,
    image_gcs_uri: str,
    image_mime_type: str,
    output_name: str,
    duration_seconds: int = 8,  # Set default to 8s
    negative_prompt: str = "",
    seed: Optional[int] = None,
) -> str:
    """
    (Internal Helper) Generates a video animated from a starting image GCS URI.
    """
    if not global_genai_client:
        return "ERROR: GenAI Client not initialized."

    print(f"Generating video from GCS image: {image_gcs_uri}")
    output_gcs_prefix = f"gs://{BUCKET_NAME}/ad_agent_outputs/"

    genai_image = types.Image(gcs_uri=image_gcs_uri, mime_type=image_mime_type)

    operation = global_genai_client.models.generate_videos(
        model=GLOBAL_VIDEO_MODEL,
        prompt=prompt,
        image=genai_image,
        config=types.GenerateVideosConfig(
            aspect_ratio="16:9",
            output_gcs_uri=output_gcs_prefix,
            number_of_videos=1,
            duration_seconds=duration_seconds,
            negative_prompt=negative_prompt,
            seed=seed,
            person_generation=types.PersonGeneration.ALLOW_ALL,
        ),
    )

    print("Waiting for video generation operation to complete...")
    while not operation.done:
        time.sleep(15)
        operation = global_genai_client.operations.get(operation)

    if (
        operation.response
        and operation.result
        and operation.result.generated_videos
        and operation.result.generated_videos[0].video
        and operation.result.generated_videos[0].video.uri
    ):
        video_uri = operation.result.generated_videos[0].video.uri
        assert video_uri is not None

        final_path = f"{output_gcs_prefix}{output_name}"
        # Replace `gsutil mv` with copy+delete using Python client
        try:
            _gcs_move(video_uri, final_path)
            print(f"Video saved to: {final_path}")
            return final_path
        except Exception as e:
            print(f"ERROR moving video in GCS: {e}")
            return f"ERROR: Failed to move generated video to final path: {e}"

    else:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("         VIDEO GENERATION FAILED       ")
        print(f"Prompt: {prompt}")
        print(f"Image: {image_gcs_uri}")
        print("Full operation details:")
        print(operation)
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return f"ERROR: Video generation failed for {image_gcs_uri}"


# ==============================================================================
# --- 4. GENERATE MUSIC AND MERGE VIDEO WITH AUDIO ---
# ==============================================================================


def _send_music_api_request(
    api_endpoint: str, data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """(Internal) Authenticates and sends a POST request to the Lyria model."""
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    access_token = creds.token

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    print(f"Sending Music API request to: {api_endpoint}")
    response = requests.post(api_endpoint, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    return response.json()


async def generate_music_from_prompt(
    music_prompt: str, tool_context: ToolContext
) -> str:
    """
    Generates a music track from a prompt, DISPLAYS IT as a playable artifact,
    saves it to GCS, and saves the GCS path to the agent's state. This is Act 3.
    """
    print(f"Generating music with prompt: '{music_prompt}'")

    music_api_endpoint = (
        f"https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}"
        f"/locations/us-central1/publishers/google/models/{AUDIO_GENERATION_MODEL_VERSION}:predict"
    )
    request_data = {"prompt": music_prompt}
    req = {"instances": [request_data], "parameters": {}}

    audio_bytes = None
    try:
        resp = _send_music_api_request(music_api_endpoint, req)
        base64_audio = resp["predictions"][0]["bytesBase64Encoded"]
        audio_bytes = base64.b64decode(base64_audio)
    except Exception as e:
        return f"ERROR: Music generation failed. {e}"

    if not audio_bytes:
        return "ERROR: Generated audio was empty."

    # --- Save to GCS and Display as Artifact ---
    audio_filename = f"soundtrack_{uuid.uuid4()}.wav"
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"ad_agent_outputs/{audio_filename}")
        blob.upload_from_string(audio_bytes, content_type="audio/wav")
        audio_gcs_path = f"gs://{BUCKET_NAME}/ad_agent_outputs/{audio_filename}"
        print(f"Music saved to GCS: {audio_gcs_path}")

        artifact_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
        await tool_context.save_artifact(audio_filename, artifact_part)
        await tool_context.load_artifact(audio_filename)
        print(f"Displayed audio artifact: {audio_filename}")

        tool_context.state["audio_gcs_path"] = audio_gcs_path
        return f"Successfully generated and displayed music. Saved to {audio_gcs_path}"

    except Exception as e:
        return f"ERROR: Failed to save or display music artifact: {e}"


async def produce_final_video_with_sound(
    output_filename: str, tool_context: ToolContext
) -> str:
    """
    Reads storyboard and music path from state, animates scenes, combines everything
    into a final video with sound, and displays it. This is the final tool (Act 4).
    """
    audio_gcs_path = tool_context.state.get("audio_gcs_path")
    if not audio_gcs_path:
        return "ERROR: Missing audio data in state."

    work = _work_dir()

    # Create a temporary filename for the silent video in /tmp/adbot
    silent_video_local_filename = os.path.join(work, f"silent_{output_filename}")

    # Produce the silent video locally
    local_silent_path = await _produce_silent_video(
        silent_video_local_filename, tool_context
    )
    if "ERROR" in local_silent_path:
        return local_silent_path  # Propagate the error

    # Merge the local silent video with the downloaded audio (all under /tmp/adbot)
    audio_local = os.path.join(work, "soundtrack.wav")
    output_with_sound_local = os.path.join(
        work, output_filename
    )  # final local output path

    try:
        # Download the audio file from GCS (replace gsutil cp)
        _gcs_download_to_file(audio_gcs_path, audio_local)

        # Merge using ffmpeg
        command = [
            "ffmpeg",
            "-i",
            local_silent_path,
            "-i",
            audio_local,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            output_with_sound_local,
            "-y",
        ]
        subprocess.run(command, check=True)

        # Upload ONLY the final video with music to GCS (replace gsutil cp)
        final_gcs_path = f"gs://{BUCKET_NAME}/ad_agent_outputs/{output_filename}"
        _gcs_upload_from_file(
            final_gcs_path, output_with_sound_local, content_type="video/mp4"
        )

        # Display the final video as an artifact
        with open(output_with_sound_local, "rb") as f:
            video_bytes = f.read()
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
        await tool_context.save_artifact(output_filename, artifact_part)
        await tool_context.load_artifact(output_filename)

        return final_gcs_path
    except Exception as e:
        return f"ERROR: Failed during final audio/video merge: {e}"
    finally:
        # Clean up all temporary local files (safe in Cloud Run /tmp)
        for f in [local_silent_path, audio_local, output_with_sound_local]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass