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

import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from ..subagents.agent_registry import get_prompt_for_industry, get_sub_agents

ORCHESTRATION_LOGIC = """
### OPERATIONAL RULES FOR SUB-AGENTS:
1. You are an orchestrator. Some of your tools are agents themselves.
2. If a tool output contains a question for the user or asks for missing information, your ONLY job is to relay that question to the user immediately.
"""

def set_system_instructions_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Set the system instructions based on the context"""

    is_custom_workflow = bool(callback_context.state.get("is_custom"))
    if is_custom_workflow:
        user_instructions = str(callback_context.state.get("custom_root_instructions", ""))
        custom_root_instructions = f"# Main Instructions\n{user_instructions}\n"

        mandatory_instructions = (
            "\n## Mandatory Instructions\n"
            "- As a first step ALWAYS the agent needs to ask each sub-agent its role and its interaction steps.\n"
            "- After this, the agent should respond to the first user interaction and provide the expected interaction."
        )
        custom_root_instructions += mandatory_instructions

        custom_agents = callback_context.state.get("custom_agents")
        if custom_agents:
            try:
                agents = get_sub_agents(custom_agents)
                if agents:
                    custom_root_instructions += "\n\n### Available Sub-agents\n"
                    for agent in agents:
                        custom_root_instructions += f"- **{agent.name}**: {agent.description}\n"
            except Exception as e:
                logging.error(f"Failed to load custom agents descriptions: {e}")

        logging.info(f"Using custom workflow with root instructions: {custom_root_instructions[:50]}...")

        # workflow_type = callback_context.state.get("type")
        custom_workflow_map = callback_context.state.get("custom_workflow_map")
        if custom_workflow_map:
            # TODO create a validation process to validate the custom_workflow_map variable, make sure that has a start and at least one
            # TODO test and improve
            workflow_prompt = f"\n\n### Sequential Workflow\nFollow this specific sequential workflow: {custom_workflow_map}"
            custom_root_instructions += workflow_prompt

        # Append orchestration rules to custom instructions
        full_instructions = str(custom_root_instructions) + ORCHESTRATION_LOGIC
        
        system_instruction = types.Content(role="system", parts=[types.Part(text=full_instructions)])
        llm_request.append_instructions(instructions=system_instruction)
    else:
        selected_industry = callback_context.state.get("industry_id")
        selected_use_case = callback_context.state.get("use_case_id")
        logging.info(f"Selected industry: {selected_industry} and use case: {selected_use_case}")
        industry_prompt = get_prompt_for_industry(selected_industry, selected_use_case)
        logging.info(f"industry_prompt: {industry_prompt}")
        
        # Append orchestration rules to industry prompt
        full_instructions = str(industry_prompt) + ORCHESTRATION_LOGIC
        
        system_instruction = types.Content(role="system", parts=[types.Part(text=full_instructions)])
        llm_request.append_instructions(instructions=system_instruction)