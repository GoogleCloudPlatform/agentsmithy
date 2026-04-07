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

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.genai import types

from .prompt import INSTRUCTION_PROMPT
from .tools.repo_analysis_tool import RepoAnalysisTools

# Initialize the custom tool class
tools_instance = RepoAnalysisTools()

tools = [
    FunctionTool(func=tools_instance.list_repository_files),
    FunctionTool(func=tools_instance.get_file_content),
]

AGENT_NAME = "discovery_agent"
AGENT_DESCRIPTION = "Analyzes legacy codebases via GitHub repositories to identify business domains, logic, and dependencies for modernization."

# Model configuration
root_agent = LlmAgent(
    model="gemini-2.5-flash",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=65536,
    ),
    name=AGENT_NAME,
    description=AGENT_DESCRIPTION,
    instruction=INSTRUCTION_PROMPT,
    tools=tools,
)
