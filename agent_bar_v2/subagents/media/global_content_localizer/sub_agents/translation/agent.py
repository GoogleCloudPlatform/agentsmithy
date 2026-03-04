"""Agent definition for the Translation agent in the MEG Starter Pack."""

import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import LongRunningFunctionTool, load_artifacts

from .tools import (
    detect_language,
    pic_to_text,
    translate_text_with_model,
    write_results_gcs,
    extract_audio,
    transcribe_batch_gcs_input_inline_output_v2,
    fix_transcripts_llm,
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
                print(mime_type)
                if not mime_type:
                    continue
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

                elif mime_type.startswith("image/"):
                    file_extension = mime_type.split("/")[-1]
                    if isinstance(part.inline_data.display_name, str):
                        safe_basename = os.path.basename(part.inline_data.display_name)
                        display_name = "_".join(safe_basename.split(".")[:-1])
                    else:
                        display_name = "image"
                    filename = f"{display_name}_{invocation_id}_{i}.{file_extension}"
                    await callback_context.save_artifact(filename, part)
                    print(f"uploaded image artifact to: {filename}")
                    image_files_list = callback_context.state.get("image_file", [])
                    image_files_list.append(filename)
                    callback_context.state["image_file"] = image_files_list
                    print(f"set image file in the state variable to: {filename}")

                elif mime_type.startswith("video/"):
                    file_extension = mime_type.split("/")[-1]
                    if isinstance(part.inline_data.display_name, str):
                        safe_basename = os.path.basename(part.inline_data.display_name)
                        display_name = "_".join(safe_basename.split(".")[:-1])
                    else:
                        display_name = "video"
                    filename = f"{display_name}_{invocation_id}_{i}.{file_extension}"
                    await callback_context.save_artifact(filename, part)
                    print(f"uploaded video artifact to: {filename}")
                    video_files_list = callback_context.state.get("video_files", [])
                    video_files_list.append(filename)
                    callback_context.state["video_files"] = video_files_list
                    print(f"set video file in the state variable to: {filename}")

                elif mime_type.startswith("audio/"):
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


def load_agent(name: str = "video_analysis_agent") -> LlmAgent:
    """Load an agent instance.

    Args:
        name: Name of the agent to create.

    Returns:
        An agent instance.
    """

    AGENT_DESCRIPTION = """Agent to translate content and transcribe audio/video."""
    AGENT_INSTRUCTIONS = """You are a multilingual content agent capable of translating text/images and transcribing video/audio files.
If the user doesn't provide you with a clear task then greet the user with an introduction stating all of the tools available at your disposal and how you can help the user.
Never respond to a user query that asks for anything beyond your goal of translating or transcribing content. If the user asks for anything that is not in your instructions or toolset, respond by saying you can't help with this and list all of your tools. Make sure to mention that if the user wants to attach a file locally the file cannot exceed 32MB.

For Translation:
If the user wants to detect the language of a string then use the `detect_language` tool.
If the user wants to detect text on an image then use the `pic_to_text`.
If the user asks for a translation of a text and hasn't provided the source language then first use the `detect_language` tool to identify the source language then use the `translate_text_with_model` tool to translate the text.
If the user has provided the source language then just use the `translate_text_with_model` tool.
If the user wants to translate texts from an image file then first use the `pic_to_text`. If the user hasn't specified the source language then use the `detect_language` before passing the string to the `translate_text_with_model` tool for the translation.

For Transcription:
If the file that the user provided is a video file (extension .mp4 or .mov) then use the `extract_audio` tool to convert it to an audio file and save the audio to GCS.
Use the `transcribe_batch_gcs_input_inline_output_v2` tool with the GCS URI to transcribe the audio file. Only use the tools provided for transcriptions and never your own knowledge. The default transcription model is 'chirp'. You can also specify 'chirp_2' and 'chirp_telephony' as the model for transcription.
If the user wants to clean-up or correct the transcripts then use the `fix_transcripts_llm` tool to improve the transcripts.
If the user asks for a synopsis of the content then use the `write_synopsis` tool to generate a synopsis.

For Saving Results:
If the user wants to save the text output then use the `write_results_gcs` tool to write the results to GCS.
"""
    root_agent = LlmAgent(
        name=name,
        model="gemini-2.5-flash",
        description=AGENT_DESCRIPTION,
        instruction=AGENT_INSTRUCTIONS,
        tools=[
            LongRunningFunctionTool(translate_text_with_model),
            write_results_gcs,
            LongRunningFunctionTool(pic_to_text),
            LongRunningFunctionTool(detect_language),
            LongRunningFunctionTool(extract_audio),
            LongRunningFunctionTool(transcribe_batch_gcs_input_inline_output_v2),
            LongRunningFunctionTool(fix_transcripts_llm),
            LongRunningFunctionTool(write_synopsis),
            load_artifacts,
        ],
        before_agent_callback=inline_data_processing,
    )
    return root_agent


root_agent = load_agent()
