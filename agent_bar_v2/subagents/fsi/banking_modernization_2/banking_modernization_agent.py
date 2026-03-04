from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import SYSTEM_INSTRUCTIONS

AGENT_DESCRIPTION = "Provides architectural guidance for modernizing legacy banking systems."

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.5, 
        top_p=0.95, 
        max_output_tokens=65536
    ),
    name="banking_modernization_architect",
    description=AGENT_DESCRIPTION,
    instruction=SYSTEM_INSTRUCTIONS,
)
