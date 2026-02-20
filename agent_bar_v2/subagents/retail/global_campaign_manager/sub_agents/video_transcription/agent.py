"""Agent definition for the Transcription Agent in the MEG Starter Pack."""

import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import LongRunningFunctionTool, load_artifacts

from .prompt import VIDEO_AGENT_INSTRUCTIONS
from .tools import (
    extract_audio,
    fix_transcripts_llm,
    transcribe_batch_gcs_input_inline_output_v2,
    write_results_gcs,
    write_synopsis,
)

load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
BUCKET_NAME = os.getenv("GCS_BUCKET")


async def inline_data_processing(callback_context: CallbackContext) -> None:
    """
    Processed any inline data files that are provided by the user and sets the state so that the data can be picked by the tools.
    """
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    user_content = callback_context.user_content

    print(f"\n[Callback] Entering agent: {agent_name} (Inv: {invocation_id})")

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

video_transcription_agent = LlmAgent(
    name="video_transcription_agent",
    model="gemini-2.5-flash",
    description="Agent to extract audio data from video files and then transcribe the audio files.",
    instruction=VIDEO_AGENT_INSTRUCTIONS,
    tools=[
        LongRunningFunctionTool(transcribe_batch_gcs_input_inline_output_v2),
        LongRunningFunctionTool(fix_transcripts_llm),
        LongRunningFunctionTool(extract_audio),
        LongRunningFunctionTool(write_results_gcs),
        LongRunningFunctionTool(write_synopsis),
        load_artifacts,
    ],
    before_agent_callback=inline_data_processing,
)
