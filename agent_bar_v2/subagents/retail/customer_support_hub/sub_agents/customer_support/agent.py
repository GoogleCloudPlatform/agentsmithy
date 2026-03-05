"""Defines the Router Agent"""

import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent

from .prompts import SYSTEM_INSTRUCTIONS
from .sub_agents import product_condition_agent, refund_issue_agent
from .tools import escalation_contact_number

_ = load_dotenv()
MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

root_agent = LlmAgent(
    name="customer_support",
    model=MODEL,
    description="""
        Greets users, triages issues and routes requests
        to the right sub-agent or escalates to human support.
    """,
    instruction=SYSTEM_INSTRUCTIONS,
    sub_agents=[product_condition_agent, refund_issue_agent],
    tools=[escalation_contact_number],
)
