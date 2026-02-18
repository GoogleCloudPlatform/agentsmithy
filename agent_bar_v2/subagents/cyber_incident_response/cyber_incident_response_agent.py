from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import SYSTEM_INSTRUCTIONS

AGENT_DESCRIPTION = "Provides initial guidance and triage for cybersecurity incidents (NIST framework)."

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.4, # Lower temperature for more deterministic/serious responses
        top_p=0.95, 
        max_output_tokens=65536
    ),
    name="cyber_incident_responder",
    description=AGENT_DESCRIPTION,
    instruction=SYSTEM_INSTRUCTIONS,
)
