import os
from google.adk.agents import LlmAgent
from .tools import acme_search_tool
from .prompt import UNSTRUCT_DATA_INSTRUCTION

from ...config import ROOT_AGENT_MODEL

unstruct_data_agent = LlmAgent(
    name="unstruct_data_agent",
    model=ROOT_AGENT_MODEL,
    output_key="acme_policy_context", 
    tools=[acme_search_tool],
    instruction=UNSTRUCT_DATA_INSTRUCTION,
    description="Extracts ACME corporate AI and FinOps policies from unstructured documents."
)