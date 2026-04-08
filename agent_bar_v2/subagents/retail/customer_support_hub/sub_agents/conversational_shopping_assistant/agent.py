<<<<<<< HEAD
import os
=======
>>>>>>> 2fb09e9f780e8e4fed2b90f3a0007e602572692b
# Copyright 2026 Google LLC
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

"""Defines Retail Concierge agent"""

from google.adk.agents import Agent
from google.adk.models import Gemini

from . import prompts
from . import tools
from .callbacks import add_citations_callback

AGENT_NAME = "conversational_shopping_assistant"
AGENT_DESCRIPTION = "Friendly retail concierge that answers user questions about Google Store products found in the catalog."

# Model configuration
GEMINI_MODEL_CONFIG = Gemini(
    model=os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
)

root_agent = Agent(
    name=AGENT_NAME,
    model=GEMINI_MODEL_CONFIG,
    description=AGENT_DESCRIPTION,
    instruction=prompts.SYSTEM_INSTRUCTION,
    tools=tools.tools,
    after_model_callback=add_citations_callback,
)
