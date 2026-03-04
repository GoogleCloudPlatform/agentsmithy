from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import SYSTEM_INSTRUCTIONS

AGENT_DESCRIPTION = "Analyzes earnings calls and financial reports to evaluate company performance, management sentiment, and strategic direction."

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.7, top_p=0.95, max_output_tokens=65536
    ),
    name="earnings_call_analytics",
    description=AGENT_DESCRIPTION,
    instruction=SYSTEM_INSTRUCTIONS,
)
