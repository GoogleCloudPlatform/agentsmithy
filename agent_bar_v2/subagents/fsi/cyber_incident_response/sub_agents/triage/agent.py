from google.adk.agents import LlmAgent
from ..tools import triageQueryTool
from .prompt import triage_agent_instruction

triage_agent = LlmAgent(
    name="triage_agent",
    description="Performs initial alert analysis and log retrieval.",
    instruction=triage_agent_instruction,
    tools=[triageQueryTool],
)
