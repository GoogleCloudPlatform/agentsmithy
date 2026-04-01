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

"""Sub-Agent definition for a specific capability."""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

# Define simple instruction inline for smaller sub-agents
INSTRUCTION = """
You are a specialized sub-agent for [Specific Capability].
Your goal is to [Specific Goal].
"""

root_agent = Agent(
    name="my_sub_agent",
    model=Gemini(
        model=os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview"),
        # Custom temperature for more creative explanations
        generation_config=types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=8192,
        ),
    ),
    instruction=INSTRUCTION,
    # This sub-agent has no tools, it relies purely on the LLM
    tools=[],
)
