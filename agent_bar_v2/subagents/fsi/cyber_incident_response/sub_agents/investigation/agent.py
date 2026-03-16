from google.adk.agents import LlmAgent
from ..tools import investigationQueryTool
from .prompt import investigation_agent_instruction

investigation_agent = LlmAgent(
    name="investigation_agent",
    description="Performs deep-dive log analysis and process correlation for detected threats.",
    instruction=investigation_agent_instruction,
    tools=[investigationQueryTool],
)
