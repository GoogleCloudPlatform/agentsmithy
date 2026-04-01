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

import os
from google.adk.agents import LlmAgent
from .prompts import SYSTEM_INSTRUCTION
from google.adk.tools import AgentTool
# Import sub-agents
from .sub_agents import customer_support_agent, conversational_shopping_assistant_agent

MODEL = os.getenv("LLM_MODEL", os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview"))
support_tool = AgentTool(customer_support_agent)
shopping_tool = AgentTool(conversational_shopping_assistant_agent)

hub_agent = LlmAgent(
    name="Customer_Support_Hub",
    description="""
        A central hub agent that routes user queries to specialized sub-agents.
        1. Customer Support: For returns, refunds, and support issues.
        2. Conversational Shopping Assistant: For product search and shopping assistance.
    """,
    instruction=SYSTEM_INSTRUCTION,
    model=MODEL,
    tools=[support_tool, shopping_tool],
)

root_agent = hub_agent