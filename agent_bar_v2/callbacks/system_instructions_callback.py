import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from ..subagents.agent_registry import get_prompt_for_industry


def set_system_instructions_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Set the system instructions based on the context"""

    is_custom_workflow = bool(callback_context.state.get("is_custom"))
    if is_custom_workflow:
        custom_root_instructions = callback_context.state.get("custom_root_instructions")
        logging.info(f"Using custom workflow with root instructions: {custom_root_instructions[:50]}...")

        # workflow_type = callback_context.state.get("type")
        custom_workflow_map = callback_context.state.get("custom_workflow_map")
        if custom_workflow_map:
            # TODO create a validation process to validate the custom_workflow_map variable, make sure that has a start and at least one
            # TODO test and improve
            workflow_prompt = f"\n\nFollow this specific sequential workflow: {custom_workflow_map}"
            custom_root_instructions += workflow_prompt

        system_instruction = types.Content(role="system", parts=[types.Part(text=str(custom_root_instructions))])
        llm_request.append_instructions(instructions=system_instruction)
    else:
        selected_industry = callback_context.state.get("industry_id")
        selected_use_case = callback_context.state.get("use_case_id")
        logging.info(f"Selected industry: {selected_industry} and use case: {selected_use_case}")
        industry_prompt = get_prompt_for_industry(selected_industry, selected_use_case)
        logging.info(f"industry_prompt: {industry_prompt}")
        system_instruction = types.Content(role="system", parts=[types.Part(text=str(industry_prompt))])
        llm_request.append_instructions(instructions=system_instruction)
