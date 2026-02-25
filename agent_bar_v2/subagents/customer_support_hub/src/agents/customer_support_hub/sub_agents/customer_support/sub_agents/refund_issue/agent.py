"""Defines the refund issue agent."""

import os

from google.adk.agents import LlmAgent

from .prompts import SYSTEM_INSTRUCTIONS
from .tools import refund_lookup_tool

MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

root_agent = LlmAgent(
    name="Refund_Issue_Agent",
    model=MODEL,
    description="""
        Assists customers with inquiries related to refunds such as
        checking on refund status.

        Does NOT support:
        * Initiating a new refund request
    """,
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[refund_lookup_tool],
)
