import os
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

"""Agent definition for the Translation agent in the MEG Starter Pack."""

from google.adk.agents import Agent
from google.adk.models import Gemini

from . import prompts
from . import tools
from .callbacks import inline_data_processing

AGENT_NAME = "translation_agent"
AGENT_DESCRIPTION = "Agent to translate content and transcribe audio/video."

# Model configuration
GEMINI_MODEL_CONFIG = Gemini(
    model=os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview"),
)

root_agent = Agent(
    name=AGENT_NAME,
    model=GEMINI_MODEL_CONFIG,
    description=AGENT_DESCRIPTION,
    instruction=prompts.SYSTEM_INSTRUCTION,
    tools=tools.tools,
    before_agent_callback=inline_data_processing,
)
