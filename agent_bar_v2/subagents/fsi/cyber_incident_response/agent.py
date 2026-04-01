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

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from .prompt import root_agent_instruction
from .sub_agents.investigation.agent import investigation_agent
from .sub_agents.response.agent import response_agent
from .sub_agents.threatintel.agent import threatintel_agent
from .sub_agents.triage.agent import triage_agent

load_dotenv()

AGENT_NAME = "cyber_incident_response"
AGENT_DESCRIPTION = "Orchestrates a multi-agent cybersecurity incident response workflow using specialized triage, investigation, threat intelligence, and response agents."


# Model configuration
GEMINI_MODEL_CONFIG = Gemini(
    model=os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
    generation_config=types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=65536,
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ],
    ),
    retry_options=types.HttpRetryOptions(attempts=3),
)

root_agent = Agent(
    name=AGENT_NAME,
    model=GEMINI_MODEL_CONFIG,
    description=AGENT_DESCRIPTION,
    instruction=root_agent_instruction,
    sub_agents=[triage_agent, investigation_agent, threatintel_agent, response_agent],
)
