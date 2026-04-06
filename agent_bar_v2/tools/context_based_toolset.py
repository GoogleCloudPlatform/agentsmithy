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
from google.adk.tools.base_toolset import BaseToolset
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_tool import BaseTool
from typing import List, Optional

from ..subagents.agent_registry import get_predefined_use_case_sub_agents, get_sub_agents



class ContextBasedToolset(BaseToolset):

    def __init__(self, prefix: str = "ctxts_"):
        self.tool_name_prefix = prefix

    async def get_tools(self, readonly_context: Optional[ReadonlyContext] = None) -> List[BaseTool]:

        logging.info("SimpleMathToolset.get_tools() called. ")

        if not readonly_context:
            return []

        is_custom_workflow = bool(readonly_context.state.get("is_custom"))

        tools_to_return = []
        try:
            if is_custom_workflow:
                custom_agents = readonly_context.state.get("custom_agents")
                logging.info(f"Using custom workflow with agents {custom_agents}")
                tools_to_return = get_sub_agents(custom_agents)
            else:
                industry_id = readonly_context.state.get("industry_id")
                use_case_id = readonly_context.state.get("use_case_id")
                logging.info(f"Getting agent for industry Id: {industry_id} and use case Id: {use_case_id}")
                tools_to_return = get_predefined_use_case_sub_agents(industry_id, use_case_id)
        except Exception as e:
            logging.error(f"Error getting agents for industry {industry_id} and use case {use_case_id}: {e}")
            logging.warning("No agents found for this industry and use case.")
            tools_to_return = []

        logging.info(f"Providing tools (agents): {[t.name for t in tools_to_return]}")
        return tools_to_return

    async def close(self) -> None:
        pass
