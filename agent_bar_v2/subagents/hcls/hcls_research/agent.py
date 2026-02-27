# Copyright 2025 Google LLC
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
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from . import prompt
from .subagents import medical_search_agent
from .subagents import hypothesis_agent
from .subagents import research_question_agent

# medical_search_tool = AgentTool(medical_search_agent)
# research_question_tool = AgentTool(research_question_agent)
# hypothesis_tool = AgentTool(hypothesis_agent)

hcls_researcher = LlmAgent(
    name="hcls_research_agent",
    model="gemini-2.5-flash",
    description=(
        """
        Root agent for producing hypotheses based on informed research
        """
    ),
    instruction=prompt.ROOT_PROMPT,
    sub_agents=[medical_search_agent, research_question_agent, hypothesis_agent],
    # tools=[medical_search_tool, research_question_tool, hypothesis_tool],
)

root_agent = hcls_researcher