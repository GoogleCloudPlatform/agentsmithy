import os
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

"""Main Agent definition for the content_archive_engine use case."""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools import load_artifacts
from google.genai import types

# Import local modules
from . import prompts
from . import tools

AGENT_NAME = "content_archive_engine"  # e.g., "insurance_claims_handler"
AGENT_DESCRIPTION = """
    The Content Archive Engine. Mission: Monetize the archives.
    1. Video Transcription creates metadata.
    2. Video Moments finds viral clips.
    """

# Model configuration
GEMINI_MODEL_CONFIG = Gemini(
    model=os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview"),
    generation_config=types.GenerateContentConfig(
        temperature=0.5,
        top_p=0.95,
        max_output_tokens=8192,
    ),
    retry_options=types.HttpRetryOptions(attempts=3),
)

root_agent = Agent(
    name=AGENT_NAME,
    model=GEMINI_MODEL_CONFIG,
    description=AGENT_DESCRIPTION,
    instruction=prompts.SYSTEM_INSTRUCTION,
    tools=[
        tools.transcription_tool,
        tools.video_analysis_tool,
        load_artifacts
    ],
)
