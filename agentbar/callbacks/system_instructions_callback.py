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

    # TODO some loggic to get details from context for example
    # user_id = callback_context.state.get("user_id")
    selected_industry = callback_context.state.get("industry_id")
    print(f"Selected industry: {selected_industry}")

    # TODO Query some database to get system instructions for that user

    industry_rules = ""
    if selected_industry == "finance":
        industry_rules = "When someone says money you must say a finance joke"
    elif selected_industry == "retail":
        industry_rules = "You are focused on Finance"
    else:
        industry_rules = "You are focused on Finance"

    system_prompt = f"""
        IMPORTANT: You must follow this rules:
            - {industry_rules}
    """

    system_instruction = types.Content(role="system", parts=[types.Part(text=str(system_prompt))])
    llm_request.append_instructions(instructions=system_instruction)
