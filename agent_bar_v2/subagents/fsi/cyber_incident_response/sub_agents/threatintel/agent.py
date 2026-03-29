from google.adk.agents import LlmAgent
from ..tools import threatIntelQueryTool
from .prompt import threatintel_agent_instruction

threatintel_agent = LlmAgent(
    name="threatintel_agent",
    description="Checks Indicators of Compromise (IoCs) against threat intelligence databases.",
    instruction=threatintel_agent_instruction,
    tools=[threatIntelQueryTool],
)
