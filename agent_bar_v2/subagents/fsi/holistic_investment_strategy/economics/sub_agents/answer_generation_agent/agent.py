# Copyright 2026 Google LLC. All Rights Reserved.
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
from injector import Injector
from ...configuration import AgentConfig

def get_answer_generation_agent(injector: Injector) -> LlmAgent:
    config = injector.get(AgentConfig)
    
    instruction = """
You are a helpful Macroeconomic Assistant. Provide a clear, technical, and data-driven 
answer to the user's question based on the JSON data retrieved from the database.

**Role:** Macroeconomic Researcher.
**Constraint:** Base your analysis ONLY on the provided data. If the data is empty or irrelevant, state that clearly.
**Format:** Provide a concise executive summary followed by key data points.
"""

    return LlmAgent(
        model="gemini-2.5-flash",
        name="AnswerGenerationAgent",
        description="Synthesizes SQL query results into a human-readable macroeconomic answer.",
        instruction=instruction,
    )
