import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from ..subagents.agent_registry import get_prompt_for_industry

# This logic instructs the Root Agent to act as a conversational proxy 
# instead of stopping after the first tool response.
ORCHESTRATION_LOGIC = """

### OPERATIONAL RULES FOR SUB-AGENTS:
1. You are an orchestrator. Some of your tools are agents themselves.
2. If a tool output contains a question for the user or asks for missing information, your ONLY job is to relay that question to the user immediately.
3. After the user answers a tool's question, you MUST call that same tool again in your next turn, passing the user's answer.
4. Do not consider a task "finished" until the sub-agent/tool provides a final result or confirmation of completion.
"""

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