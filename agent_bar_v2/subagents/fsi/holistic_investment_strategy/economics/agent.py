from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import SYSTEM_INSTRUCTIONS

AGENT_DESCRIPTION = "Analyzes global economic trends, central bank policies, and market indicators to provide macroeconomic insights."

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.7, top_p=0.95, max_output_tokens=65536
    ),
    name="macroeconomic_researcher",
    description=AGENT_DESCRIPTION,
    instruction=SYSTEM_INSTRUCTIONS,
)
