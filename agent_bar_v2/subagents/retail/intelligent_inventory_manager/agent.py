# ruff: noqa
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

import datetime
import os
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
import google.auth

from .prompts import SYSTEM_INSTRUCTION
from .sub_agents.nl2sql.agent import nl2sql_agent
from .sub_agents.catalog_enrichment.agent import catalog_enrichment_agent



root_agent = Agent(
        name="intelligent_inventory_manager",
        model=os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
        description=(
            "You are an Intelligent Inventory Manager Agent, a helpful AI "
            "agent that can manage inventory for retail companies. "
        ),
        instruction=SYSTEM_INSTRUCTION,
        sub_agents=[nl2sql_agent, catalog_enrichment_agent],
    )
