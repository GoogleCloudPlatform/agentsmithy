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

"""Main Agent definition for the [Use Case Name] use case."""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools import AgentTool
from google.genai import types

# Import local modules
from . import prompts
from . import tools
from .sub_agents.my_sub_agent.agent import root_agent as my_sub_agent

AGENT_NAME = "agent_template_name"  # e.g., "insurance_claims_handler"
AGENT_DESCRIPTION = "Handles specific use case requests and delegates to sub-agents as needed."

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
        tools.calculate_metric,
        # You can also add sub-agents as tools if you want the parent to retain control:
        # AgentTool(my_sub_agent),
    ],
    sub_agents=[
        my_sub_agent,
    ],
)
