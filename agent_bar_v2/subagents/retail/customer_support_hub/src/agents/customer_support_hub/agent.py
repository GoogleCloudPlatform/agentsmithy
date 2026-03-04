import os
from google.adk.agents import LlmAgent
from .prompts import SYSTEM_INSTRUCTIONS
from google.adk.tools import AgentTool
# Import sub-agents
from .sub_agents import customer_support_agent, conversational_shopping_assistant_agent

MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
support_tool = AgentTool(customer_support_agent)
shopping_tool = AgentTool(conversational_shopping_assistant_agent)

hub_agent = LlmAgent(
    name="Customer_Support_Hub",
    description="""
        A central hub agent that routes user queries to specialized sub-agents.
        1. Customer Support: For returns, refunds, and support issues.
        2. Conversational Shopping Assistant: For product search and shopping assistance.
    """,
    instruction=SYSTEM_INSTRUCTIONS,
    model=MODEL,
    tools=[support_tool, shopping_tool],
)

root_agent = hub_agent