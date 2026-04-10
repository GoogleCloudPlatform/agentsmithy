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

"""Main Agent definition for the meeting_intelligence use case."""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools import load_artifacts
from google.genai import types

# Import local modules
from . import prompts
from . import tools

AGENT_NAME = "meeting_intelligence"
AGENT_DESCRIPTION = """
    The Meeting Intelligence Agent. Mission: Summarize town halls to make corporate knowledge searchable and accessible.
    """

from agent_bar_v2.subagents.utils.model import get_gemini_config

# Model configuration
GEMINI_MODEL_CONFIG = get_gemini_config()

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
