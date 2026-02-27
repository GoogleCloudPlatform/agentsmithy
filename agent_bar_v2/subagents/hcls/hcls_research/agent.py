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
import sys
import os
from google.adk.agents import LlmAgent

shared_utility = os.path.abspath("../../subagents/")

print(shared_utility)

if shared_utility not in sys.path:
    sys.path.append(shared_utility)

from . import prompt
from .subagents import medical_search_agent
from subagents.utility import hypothesis_agent
from subagents.utility import research_question_agent

hcls_researcher = LlmAgent(
    name="hcls_research_agent",
    model="gemini-2.5-flash",
    description=(
        "Creates research hypotheses for research questions"
        " based on pubmed search results."
    ),
    instruction=prompt.ROOT_PROMPT,
    sub_agents=[research_question_agent, medical_search_agent, hypothesis_agent],
)

root_agent = hcls_researcher