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

"""Tools for Transcription Agent"""

import json
import os
import subprocess
import tempfile
import time
import uuid

import google.cloud.storage as storage
from dotenv import load_dotenv
from fpdf import FPDF
from google import genai
from google.adk.tools import ToolContext
from google.api_core import client_options
from google.cloud import speech_v2 as cloud_speech
from google.genai import types

from ...config import PROJECT_ID, LOCATION, BUCKET_NAME

GCS_OUTPUT_PATH = "transcription_agent_output"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_SPEECH_MODEL = "chirp"
VALID_STT_MODELS = {"chirp", "chirp_2", "chirp_telephony"}


async def extract_audio(
    tool_context: ToolContext, video_gcs_uri: str = "", artifact_name: str = ""
) -> dict:
    """
    Extracts audio from a video file, uploads it to GCS, and cleans up local files.

    The function handles video input from either a locally uploaded artifact or a
    GCS URI. It uses a temporary directory to manage all local file operations,
    ensuring automatic cleanup even if errors occur.

    Args:
        video_gcs_uri: GCS URI for the video file.
        tool_context (ToolContext): Contains the state, including any uploaded files.
        artifact_name (str): Path to a local artifact uploaded by the user.

    Returns:
        A dictionary with the status and the GCS URI of the extracted audio file.
    """
    # Use a temporary directory for all local files; it's automatically cleaned up.
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_client = storage.Client()
        source_file_path = None

        try:
            # --- Step 1: Get the video file onto the local filesystem ---
            filenames = tool_context.state.get("video_files")
            if not artifact_name and filenames:
                artifact_name = filenames[-1]

            if artifact_name:
                video_part = await tool_context.load_artifact(artifact_name)
                if (
                    not video_part
                    or not video_part.inline_data
                    or not video_part.inline_data.data
                ):
                    return {"status": "error", "message": "No data in artifact."}

                source_file_path = os.path.join(temp_dir, artifact_name)
                with open(source_file_path, "wb") as f:
                    f.write(video_part.inline_data.data)

            elif video_gcs_uri:
                bucket_name, blob_name = video_gcs_uri[5:].split("/", 1)
                source_filename = os.path.basename(blob_name)
                source_file_path = os.path.join(temp_dir, source_filename)

                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.download_to_filename(source_file_path)
            else:
                return {
                    "status": "error",
                    "message": "Please provide a video file to process.",
                }

            # --- Step 2: Extract audio using ffmpeg ---
            base, _ = os.path.splitext(os.path.basename(source_file_path))
            output_filename = f"{base}.wav"
            output_file_path = os.path.join(temp_dir, output_filename)

            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    source_file_path,
                    "-vn",  # No video output
                    "-acodec",
                    "pcm_s16le",  # Standard WAV audio codec
                    "-ar",
                    "16000",  # 16kHz sample rate (optimal for STT)
                    "-ac",
                    "1",  # Mono channel (optimal for STT)
                    output_file_path,
                ],
                check=True,
                capture_output=True,
            )  # capture_output suppresses console logs

            # --- Step 3: Upload the extracted audio file to GCS ---
            gcs_path = f"{GCS_OUTPUT_PATH}/{output_filename}"
            dest_bucket = storage_client.bucket(BUCKET_NAME)
            dest_blob = dest_bucket.blob(gcs_path)
            dest_blob.upload_from_filename(output_file_path)

            return {
                "status": "success",
            }

        except subprocess.CalledProcessError:
            # Catches errors specifically from the ffmpeg command
            return {
                "status": "error",
                "message": "Audio extraction failed due to an internal error.",
            }
        except Exception:
            # Catches all other errors (GCS download, file write, etc.)
            return {
                "status": "error",
                "message": "An unexpected error occurred during audio extraction.",
            }


async def transcribe_batch_gcs_input_inline_output_v2(
    language: str,
    tool_context: ToolContext,
    audio_gcs_uri: str = "",
    artifact_name: str = "",
    model: str = DEFAULT_SPEECH_MODEL,
    output_format: str = "native",
) -> dict:
    """Transcribes ALL audio from a Google Cloud Storage URI using the Speech-to-Text V2 API.
    The input can be an audio_gcs_uri or it might be a local file upload where the GCS URI is available in the tool_context state.

    Args:
        audio_gcs_uri: The Google Cloud Storage URI of the audio file starting with `gs://`
        tool_context: Contains the state, including the GCS URIs of any uploaded local files.
        language: Language for the audio file
        model: STT model to be used
        output_format: `native` if the user wants text output. `vtt` if the user wants VTT output.
        artifact_name: Path to a local artifact uploaded by the user.

    Returns:
        dict: A dictionary with the status and in case of success the transcribed text.
    """
    # Determine the artifact name if not explicitly provided
    filenames = tool_context.state.get("audio_files")
    if not artifact_name and filenames:
        artifact_name = filenames[-1]

    # If a local file (artifact) is provided, upload it to GCS first.
    if artifact_name:
        try:
            audio_part = await tool_context.load_artifact(artifact_name)

            # More robust check to ensure audio data exists.
            if (
                not audio_part
                or not audio_part.inline_data
                or not audio_part.inline_data.data
            ):
                return {
                    "status": "error",
                    "message": "Could not load data from the provided artifact.",
                }

            audio_bytes = audio_part.inline_data.data

            storage_client = storage.Client()
            bucket = storage_client.bucket(BUCKET_NAME)

            # Define a clear path for the uploaded file
            blob_path = f"{GCS_OUTPUT_PATH}/{artifact_name}"
            blob = bucket.blob(blob_path)

            blob.upload_from_string(
                audio_bytes, content_type=audio_part.inline_data.mime_type
            )

            # Set the GCS URI to the newly uploaded file.
            audio_gcs_uri = f"gs://{BUCKET_NAME}/{blob_path}"

        except Exception:
            return {
                "status": "error",
                "message": "Could not upload the audio file to GCS.",
            }

    # Final check: At this point, we must have a GCS URI to proceed.
    if not audio_gcs_uri:
        return {
            "status": "error",
            "message": "Please provide the audio you want to transcribe by uploading a file or specifying a gs:// URI.",
        }

    # Validate the selected STT model
    if model not in VALID_STT_MODELS:
        return {
            "status": "error",
            "message": f"Invalid STT model selected. Please choose one of: {', '.join(sorted(list(VALID_STT_MODELS)))}",
        }

    # Determine the API endpoint based on the location. "global" uses the default.
    if output_format not in ["native", "vtt"]:
        return {
            "status": "error",
            "message": "The only valid output types for a transcription is native text or vtt.",
        }
    file_path = os.path.join(os.path.dirname(__file__), "transcription_codes.json")
    with open(file_path, "r", encoding="utf-8") as f:
        language_codes = json.load(f)

    if language.lower() in language_codes:
        language = language_codes[language.lower()]
    elif language not in language_codes.values():
        return {"status": "error", "message": "Provide a valid language."}

    endpoint = "speech.googleapis.com"
    if LOCATION != "global":
        endpoint = f"{LOCATION}-{endpoint}"

    # Configure client options, specifically setting the API endpoint.
    options = client_options.ClientOptions(api_endpoint=endpoint)

    # Create the Speech-to-Text client using the configured options.
    client = cloud_speech.SpeechClient(client_options=options)

    # 2. Configure Recognition Features.
    # Enables word time offsets and separates recognition per audio channel.
    # All relevant features to be included in the output transcript should be added here:
    recognition_features = cloud_speech.RecognitionFeatures(
        enable_word_time_offsets=True,
        multi_channel_mode=cloud_speech.RecognitionFeatures.MultiChannelMode.SEPARATE_RECOGNITION_PER_CHANNEL,
    )

    # 3. Configure Recognition Settings.
    # Sets the audio decoding, language, model, and features.
    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=[language],  # Specify the language of the audio.
        model=model,  # Select the model most appropriate for your use-case
        features=recognition_features,  # Use the configured features.
    )

    # 4. Define the audio file metadata.
    # Specifies the GCS URI of the audio file to be transcribed.
    file_metadata = cloud_speech.BatchRecognizeFileMetadata(uri=audio_gcs_uri)

    # 5. Create the BatchRecognizeRequest.
    # This request includes the recognizer, configuration, audio file metadata, and output settings.
    if output_format == "vtt":
        output_format_config = cloud_speech.OutputFormatConfig(
            vtt=cloud_speech.VttOutputFileFormatConfig()
        )
    else:
        output_format_config = None

    request = cloud_speech.BatchRecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/{LOCATION}/recognizers/_",
        config=config,
        files=[file_metadata],
        recognition_output_config=cloud_speech.RecognitionOutputConfig(
            inline_response_config=cloud_speech.InlineOutputConfig(),
            output_format_config=output_format_config,
        ),
    )

    # 6. Submit the Batch Recognition job.
    # Sends the request to the Speech-to-Text API and starts the transcription process.
    try:
        operation = client.batch_recognize(request=request)

        # 7. Wait for the operation to complete and get the response.
        response = operation.result(timeout=3600)
    except Exception:
        print("Could not transcribe audio file.")
        return {"status": "error", "message": "Could not transcribe the audio file."}

    # 8. Function to sort the transcription results by time offset.
    def sort_batch_output(
        response: cloud_speech.BatchRecognizeResults,
    ) -> list[tuple[float, str]]:
        time_offset_transcript = {}
        for res in response:
            if (
                res.alternatives
                and hasattr(res.alternatives[0], "transcript")
                and hasattr(res.alternatives[0], "words")
                and res.alternatives[0].words
            ):
                for word in res.alternatives[0].words:  # Loop through words.
                    time_code = word.end_offset.seconds + (
                        word.end_offset.microseconds / 1000000
                    )
                    time_offset_transcript[time_code] = word.word
        return sorted(time_offset_transcript.items())  # Return sorted list of tuples.

    # 9. Process and format the transcription results.å
    if output_format == "vtt":
        transcript = response.results[audio_gcs_uri].inline_result.vtt_captions
    else:
        sorted_result = sort_batch_output(
            response.results[audio_gcs_uri].transcript.results
        )
        transcript = " ".join(
            [i[1] for i in sorted_result]
        )  # Create a string of the transcript.

    # 10. Return the final transcribed text.
    return {"status": "success", "transcript": transcript}


async def fix_transcripts_llm(
    tool_context: ToolContext,
    transcript: str = "",
    gemini_model: str = DEFAULT_GEMINI_MODEL,
) -> dict:
    """Use LLMs to clean-up the language of the transcript including grammar fixes and any
    possible insertion, deletion or substitution errors that may have
    occurred during the transcription.

    Args:
        transcript (str): The transcript to be cleaned up.
        gemini_model (str): Gemini model to use for processing.
        tool_context (ToolContext): Contains the state, including any uploaded files.

    Returns:
        dict: A dictionary with the status and in case of success the fixed transcript
    """
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    prompt = """You are a speech-to-text transcription improvement assistant tasked with correcting grammatical errors in a dialogue transcript.
Your goal is to analyze the raw transcript produced by automatic speech recognition systems, identify any inaccuracies stemming from mistranscriptions
and refine the text to ensure it is grammatically correct with easy readability.

Here's how to approach the task step by step:

1. **Careful Evaluation:** Start by carefully reading through the transcript. Pay close attention to context and syntax to catch and comprehend any potential inaccuracies.
2. **Grammar Correction:** Check the tense of the sentence and correct it if the tense of a verb is not consistent with the remainder of the sentence.
3. **Deletion Errors:** Words might be missing from the transcript due to a deletion error caused by the ASR system. If there are words that appear to be missing in the context of the dialogue, insert these words without changing the meaning of the dialogue. Be conservative in your insertions and don't input any word or phrase that would deviate from the meaning of the input transcript.
4. **Pronoun and Article Correction:** If there is a pronoun or an article missing in the sentence ensure to insert the correct word by referring to the context of the dialogue.
5. **Repetition Removal:** Remove any mumblings or repetitions in the transcript that cause redundancies.
6. **Homophone Clarification:** Look out for words that sound alike but are spelled differently ('there' vs 'their') and replace the word in the transcript with its homophone if the homophone is more relevant in the given context of the transcript.
7. **Coverage:** Make sure to review every single sentence in the transcript closely and make any necessary corrections. Don't make any other changes to the text that might alter the meaning.
7. **Output Format:** Output the transcript with all relevant corrections. Don't provide any explanations for the corrections.

Original: {transcript}
Corrected Transcript:"""

    prompt_with_data = prompt.format(transcript=transcript)

    max_number_retries = 2
    retry_time = 2
    retries = 0
    # attempt to generate gemini response with exponential backoff
    while retries <= max_number_retries:
        try:
            response = client.models.generate_content(
                model=gemini_model,
                contents=[
                    prompt_with_data,
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                ),
            )
            return {"status": "success", "corrected_transcript": response.text}
        except Exception:
            print("Waiting 60 seconds to try again...")
            time.sleep(retry_time)
            retry_time = retry_time * 2
            retries += 1
    print("Gemini could not annotate file.")
    return {"status": "error", "message": "Gemini could not correct the transcript."}


async def write_results_gcs(
    transcript: str, output_format: str, file_name: str = ""
) -> dict:
    """Write the resulting script to GCS.
    Args:
        file_name (str): Name of the original file being processed.
        transcript (str): The transcript to be written to GCS
        output_format (str): `txt`, `vtt` or `pdf` formats.
    Returns:
        dict: Dictionary with the status and if success the GCS URI to the file written to GCS
    """
    if output_format.lower() not in ["txt", "pdf", "vtt"]:
        return {
            "status": "error",
            "message": "Invalid output_format. Must be 'txt' or 'pdf'.",
        }

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    # Generate a unique filename using UUID
    if not file_name:
        unique_id = uuid.uuid4()
        file_name = f"output_{unique_id}"

    try:
        if output_format.lower() == "txt":
            file_extension = ".txt"
            gcs_blob_name = f"{GCS_OUTPUT_PATH}/{file_name}{file_extension}"

            # Create a Blob object and upload string directly to GCS
            blob = bucket.blob(gcs_blob_name)
            blob.upload_from_string(transcript, content_type="text/plain")

            print("Successfully uploaded text file to GCS.")
            return {
                "status": "success",
            }

        elif output_format.lower() == "vtt":
            file_extension = ".vtt"
            gcs_blob_name = f"transcripts/{file_name}{file_extension}"

            # Create a Blob object and upload string directly to GCS
            blob = bucket.blob(gcs_blob_name)
            blob.upload_from_string(transcript, content_type="text/vtt")

            print("Successfully uploaded text file to GCS.")
            return {
                "status": "success",
            }

        else:
            file_extension = ".pdf"
            gcs_blob_name = f"transcripts/{file_name}{file_extension}"

            # Create PDF in-memory (BytesIO) or a temporary local file
            # For simplicity and robustness with FPDF, let's use a temporary local file
            # In a serverless environment (e.g., Cloud Functions), ensure /tmp is writable
            local_temp_file_path = os.path.join("/tmp", f"{file_name}{file_extension}")

            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                # FPDF's multi_cell handles line breaks automatically
                pdf.multi_cell(0, 10, txt=transcript)
                pdf.output(local_temp_file_path)  # Save PDF to a temporary local file

                # Upload the local PDF file to GCS
                blob = bucket.blob(gcs_blob_name)
                blob.upload_from_filename(
                    local_temp_file_path, content_type="application/pdf"
                )

                print("Successfully uploaded PDF file to GCS.")
                return {
                    "status": "success",
                }
            finally:
                if os.path.exists(local_temp_file_path):
                    os.remove(local_temp_file_path)
                    print("Successfully deleted temporary file.")
    except Exception:
        print("An error occurred.")
        return {"status": "error", "message": "Failed to write results to GCS."}


async def write_synopsis(
    tool_context: ToolContext,
    artifact_name: str = "",
    transcript: str = "",
    gcs_uri: str = "",
    gemini_model: str = DEFAULT_GEMINI_MODEL,
) -> dict:
    """Use LLMs to generate synopsis for media transcripts.
    The media transcripts can be provided as strings or a GCS URI can be provided
    to a text file containing the transcript.

    Args:
        gcs_uri (str): The GCS URI to the text file containing the transcript.
        transcript (str): The transcript that needs a synopsis.
        gemini_model (str): Gemini model to use for processing.
        artifact_name (str): Path to a local artifact uploaded by the user.
        tool_context (ToolContext): Contains the state, including any uploaded files.

    Returns:
        dictionary: Dictionary containing status and if success the synopsis of the transcript.
    """
    if not transcript and artifact_name:
        txt_part = await tool_context.load_artifact(artifact_name)
        if txt_part and txt_part.inline_data and txt_part.inline_data.data:
            transcript = txt_part.inline_data.data.decode("utf-8")
    if not transcript and gcs_uri:
        try:
            storage_client = storage.Client()
            path_parts = gcs_uri[5:].split("/", 1)
            bucket_name = path_parts[0]
            blob_name = path_parts[1]
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            if blob.name.endswith((".txt")):
                transcript = blob.download_as_text()
            else:
                return {
                    "status": "error",
                    "message": "Provide the GCS URI to a valid text file.",
                }

        except Exception:
            return {
                "status": "error",
                "message": "Provide the GCS URI to a valid text file.",
            }
    if not transcript:
        filenames = tool_context.state.get("text_files")
        if filenames:
            latest_file = filenames[-1]
            txt_part = await tool_context.load_artifact(latest_file)
            if txt_part and txt_part.inline_data and txt_part.inline_data.data:
                transcript = txt_part.inline_data.data.decode("utf-8")
                print("Captured txt data from state")
            else:
                return {"status": "error", "message": "Provide the transcript."}
        else:
            return {"status": "error", "message": "Provide the transcript."}
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    prompt = """You are an expert in content marketing. Given the transcript to a media file, generate a 2-4 sentences long synopsis for the video.
The synopsis has to give a short overview of what is happening in the video.
The language should be engaging and should inspire all types of customers to watch the video without giving away the ending.
Transcript: {transcript}
Synopsis:"""

    prompt_with_data = prompt.format(transcript=transcript)

    max_number_retries = 2
    retry_time = 2
    retries = 0
    # attempt to generate gemini response with exponential backoff
    while retries <= max_number_retries:
        try:
            response = client.models.generate_content(
                model=gemini_model,
                contents=[
                    prompt_with_data,
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                ),
            )
            return {"status": "success", "synopsis": response.text}
        except Exception:
            print("Waiting 60 seconds to try again...")
            time.sleep(retry_time)
            retry_time = retry_time * 2
            retries += 1
    print("Gemini could not annotate file.")
    return {"status": "error", "message": "Gemini could not correct the transcript."}
