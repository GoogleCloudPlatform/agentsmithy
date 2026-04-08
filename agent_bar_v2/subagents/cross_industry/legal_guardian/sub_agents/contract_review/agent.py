<<<<<<< HEAD
import os
=======
>>>>>>> 2fb09e9f780e8e4fed2b90f3a0007e602572692b
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

"""Main Agent definition for the Contract Review use case."""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

# Import local modules
from . import prompts
from . import tools

AGENT_NAME = "contract_review"
AGENT_DESCRIPTION = "Reviews and provides feedback on contracts, SOWs, and proposals based on best practices."

# Model configuration
GEMINI_MODEL_CONFIG = Gemini(
    model=os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
    generation_config=types.GenerateContentConfig(
        temperature=0.8,
        top_p=0.95,
        max_output_tokens=65536,
    ),
)

root_agent = Agent(
    name=AGENT_NAME,
    model=GEMINI_MODEL_CONFIG,
    description=AGENT_DESCRIPTION,
    instruction=prompts.SYSTEM_INSTRUCTION,
    tools=tools.tools,
)
