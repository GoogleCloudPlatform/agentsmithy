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

from google.adk.agents import Agent
from google.adk.models import Gemini

from . import prompts
from . import tools

AGENT_NAME = "Product_Condition_Agent"
AGENT_DESCRIPTION = """
        Assists customers with returning items that present some issue. Issues include:
        * Incorrect item received
        * Issue physical state or functional quality of a product,
        product defects, performance, or poor quality.

        Does NOT support:
        * Missing items from order
    """

GEMINI_MODEL_CONFIG = Gemini(
    model="gemini-2.5-flash",
)

root_agent = Agent(
    name=AGENT_NAME,
    model=GEMINI_MODEL_CONFIG,
    description=AGENT_DESCRIPTION,
    instruction=prompts.SYSTEM_INSTRUCTION,
    tools=tools.tools,
)
