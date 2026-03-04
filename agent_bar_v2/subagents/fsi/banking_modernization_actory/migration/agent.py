from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import SYSTEM_INSTRUCTIONS

AGENT_DESCRIPTION = "Translates Oracle schemas and PL/SQL to BigQuery compatible SQL, optimizing for the cloud environment."

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2, top_p=0.95, max_output_tokens=65536
    ),
    name="oracle_to_bigquery",
    description=AGENT_DESCRIPTION,
    instruction=SYSTEM_INSTRUCTIONS,
)
