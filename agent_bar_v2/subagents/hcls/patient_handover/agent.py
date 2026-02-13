"""Entrypoint for the patient handover agent."""

import os
from datetime import datetime

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext

from . import tools


def initialize_state(callback_context: CallbackContext) -> None:
    start_time = datetime.strptime("2024-06-07 07:30:00", "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime("2024-06-07 19:30:00", "%Y-%m-%d %H:%M:%S")

    callback_context.state["shifts"] = [
        {"start_time": start_time.isoformat(), "end_time": end_time.isoformat()}
    ]
    callback_context.state["patients"] = ["MHID123456789"]

    callback_context.state["section_model"] = os.environ.get(
        "SECTION_MODEL_NAME", "gemini-2.5-flash"
    )
    callback_context.state["summary_model"] = os.environ.get(
        "SUMMARY_MODEL_NAME", "gemini-2.5-flash"
    )


def load_agent(name: str = "patient_handover_assistant") -> LlmAgent:
    """Load an agent instance.

    Args:
        name: Name of the agent to create.

    Returns:
        An agent instance.
    """

    return LlmAgent(
        name=name,
        instruction="""
You are a patient shift handover / endorsement assistant.
Your goal is to help the user generate a report for the shift that they request.
Always make sure to look up what shifts and patients are available before attempting to generate an endorsement report.
When the user starts the conversation, greet them and briefly state your purpose for being a patient handover assistant that helps streamline the shift handover process by automatically generating a comprehensive reports. Use your tools to mention the shifts and patients after greeting.
""".strip(),
        model=os.environ.get("AGENT_MODEL_NAME", "gemini-2.5-flash"),
        before_agent_callback=initialize_state,
        tools=[
            tools.list_available_shifts,
            tools.list_patients,
            tools.generate_shift_endorsement,
        ],
    )


root_agent = load_agent()