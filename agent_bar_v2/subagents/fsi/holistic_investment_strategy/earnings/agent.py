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

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from . import prompts
from . import tools


AGENT_NAME = "earnings_call_analytics"
AGENT_DESCRIPTION = "Analyzes earnings calls and financial reports to evaluate company performance, management sentiment, and strategic direction."


# Model configuration
GEMINI_MODEL_CONFIG = Gemini(
    model="gemini-2.5-flash",
    generation_config=types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        max_output_tokens=65536,
    ),
    retry_options=types.HttpRetryOptions(attempts=3),
)

root_agent = Agent(
    name=AGENT_NAME,
    model=GEMINI_MODEL_CONFIG,
    description=AGENT_DESCRIPTION,
    instruction=prompts.SYSTEM_INSTRUCTION,
    tools=tools.tools,
)
