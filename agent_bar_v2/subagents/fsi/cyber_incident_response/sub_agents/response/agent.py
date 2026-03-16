from google.adk.agents import LlmAgent
from ..tools import getPlaybookTool, responseExecutionTool, createIncidentTool
from .prompt import response_agent_instruction

response_agent = LlmAgent(
    name="response_agent",
    description="Recommends and executes mitigation actions based on playbooks.",
    instruction=response_agent_instruction,
    tools=[getPlaybookTool, responseExecutionTool, createIncidentTool],
)
