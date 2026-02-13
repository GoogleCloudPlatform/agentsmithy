from google.adk.agents import LlmAgent
from google.adk.tools import load_artifacts
from google.genai import types

from .prompt import SYSTEM_INSTRUCTIONS

AGENT_DESCRIPTION = ""

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.8, top_p=0.95, max_output_tokens=65536
    ),
    name="weather_agent",
    description=AGENT_DESCRIPTION,
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[load_artifacts],
)
