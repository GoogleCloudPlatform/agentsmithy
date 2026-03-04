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

"""HCLS Research Agent for supporting researchers with pubmed access."""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from . import prompts
from . import tools

from .subagents.hypothesis_agent import hypothesis_agent
from .subagents.research_question_agent import research_question_agent
from .subagents.search_agent import search_agent

AGENT_NAME = "hcls_research_agent"
AGENT_DESCRIPTION = (
    "Creates research hypotheses for research questions"
    " based on pubmed search results."
)

# Model configuration
GEMINI_MODEL_CONFIG = Gemini(
    model="gemini-2.5-flash",
)

root_agent = Agent(
    name=AGENT_NAME,
    model=GEMINI_MODEL_CONFIG,
    description=AGENT_DESCRIPTION,
    instruction=prompts.SYSTEM_INSTRUCTION,
    tools=tools.tools,
    sub_agents=[research_question_agent, search_agent, hypothesis_agent],
)