from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types


def set_system_instructions_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Set the system instructions bassed on the context"""

    # agent_name = callback_context.agent.name
    # log.debug(f"Setting system instructions for {agent_name}")
    from ..industry_prompts import get_prompt_for_industry

    selected_industry = callback_context.state.get("industry_id")
    print(f"Selected industry: {selected_industry}")

    industry_prompt = get_prompt_for_industry(selected_industry)
    system_instruction = types.Content(role="system", parts=[types.Part(text=str(industry_prompt))])
    llm_request.append_instructions(instructions=system_instruction)
