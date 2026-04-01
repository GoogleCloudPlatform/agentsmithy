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

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from .prompt import SYSTEM_INSTRUCTIONS
from .economics.agent import root_agent as macro_agent
from .earnings.agent import root_agent as earnings_agent
from .finsights.agent import root_agent as finsights_agent

AGENT_DESCRIPTION = "Orchestrates a holistic investment strategy by combining macroeconomic research, earnings analysis, and quantitative screening."

root_agent = LlmAgent(
    model=os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview"),
    generate_content_config=types.GenerateContentConfig(
        temperature=0.7, top_p=0.95, max_output_tokens=65536
    ),
    name="holistic_investment_strategy",
    description=AGENT_DESCRIPTION,
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[
        AgentTool(macro_agent),
        AgentTool(earnings_agent),
        AgentTool(finsights_agent),
    ],
)
