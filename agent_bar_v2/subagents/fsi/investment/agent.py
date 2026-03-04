from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from .prompt import SYSTEM_INSTRUCTIONS
from .economics.agent import root_agent as macro_agent
from .earnings.agent import root_agent as earnings_agent
from .finsights.agent import root_agent as finsights_agent

AGENT_DESCRIPTION = "Orchestrates a holistic investment strategy by combining macroeconomic research, earnings analysis, and quantitative screening."

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.7, top_p=0.95, max_output_tokens=65536
    ),
    name="holistic_investment_strategy",
    description=AGENT_DESCRIPTION,
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[
        AgentTool(macro_agent),
        AgentTool(earnings_agent),
        AgentTool(finsights_agent),
    ],
)
