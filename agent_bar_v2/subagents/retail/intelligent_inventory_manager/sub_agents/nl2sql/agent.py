import os
"""Defining the NL2SQL agent."""

from google.adk.agents import Agent

from .prompts import SYSTEM_INSTRUCTIONS
from .tools import product_selection, search_product_table_v2, store_locator


nl2sql_agent = Agent(
    name="nl2sql",
    model=os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview"),
    description=("Agent to answer question about retail products."),
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[search_product_table_v2, store_locator, product_selection],
)
