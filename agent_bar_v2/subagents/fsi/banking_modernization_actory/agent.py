from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from .prompt import SYSTEM_INSTRUCTIONS
from .discovery.agent import root_agent as discovery_agent
from .migration.agent import root_agent as migration_agent

AGENT_DESCRIPTION = "Orchestrates the modernization of legacy banking cores using domain discovery and cloud migration tools."

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2, top_p=0.95, max_output_tokens=65536
    ),
    name="banking_modernization_factory",
    description=AGENT_DESCRIPTION,
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[
        AgentTool(discovery_agent),
        AgentTool(migration_agent),
    ],
)
