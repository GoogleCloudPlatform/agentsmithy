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

import logging
from google.adk.agents.llm_agent import Agent

from .callbacks.system_instructions_callback import (
    set_system_instructions_callback,
)

from .tools.context_based_toolset import ContextBasedToolset

logging.basicConfig(level=logging.INFO)

context_based_toolset = ContextBasedToolset()

root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="",
    instruction="",
    before_model_callback=set_system_instructions_callback,
    tools=[context_based_toolset]
)
