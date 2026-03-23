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

"""Main Agent definition for the Global Content Localizer use case."""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools import AgentTool
from google.genai import types

# Import local modules
from . import prompts
from . import tools
from .sub_agents.translation.agent import root_agent as translation_agent

AGENT_NAME = "global_content_localizer"
AGENT_DESCRIPTION = "Expands streaming reach by generating subtitles and localized content for new regions."

# Model configuration
GEMINI_MODEL_CONFIG = Gemini(
    model="gemini-2.5-flash",
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
        # Registering the sub-agent as a tool gives it more flexibility if desired,
        # but listing it in sub_agents is the standard way for delegation.
        # We can do both if we want the parent to be able to "call" it as a tool too.
        # For now, let's keep it simple with sub_agents list.
    ],
    sub_agents=[
        translation_agent,
    ],
)
