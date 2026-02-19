import os

from google.adk.agents import LlmAgent

from .prompts import SYSTEM_INSTRUCTIONS
from .tools import get_all_store_data, is_valid_email

MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

root_agent = LlmAgent(
    name="Product_Condition_Agent",
    model=MODEL,
    description="""
        Assists customers with returning items that present some issue. Issues include:
        * Incorrect item received
        * Issue physical state or functional quality of a product,
        product defects, performance, or poor quality.

        Does NOT support:
        * Missing items from order
    """,
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[get_all_store_data, is_valid_email],
)
