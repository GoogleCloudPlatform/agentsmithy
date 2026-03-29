from dotenv import load_dotenv
from google.adk.agents import LlmAgent

from .prompt import root_agent_instruction
from .sub_agents.investigation.agent import investigation_agent
from .sub_agents.response.agent import response_agent
from .sub_agents.threatintel.agent import threatintel_agent
from .sub_agents.triage.agent import triage_agent

load_dotenv()

AGENT_DESCRIPTION = "Orchestrates a multi-agent cybersecurity incident response workflow using specialized triage, investigation, threat intelligence, and response agents."

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="cyber_guardian_orchestrator",
    description=AGENT_DESCRIPTION,
    instruction=root_agent_instruction,
    sub_agents=[triage_agent, investigation_agent, threatintel_agent, response_agent],
)
