from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import AGENT_INSTRUCTION
from .tools.sql_translation import (
    analyze_sql_with_gemini_tool,
    check_error_files_tool,
    mapping_tool,
    resolve_sql_error_tool,
    run_sql_translation_tool,
    upload_to_gcs_tool,
)

AGENT_DESCRIPTION = "An agent that translates SQL queries between different dialects using BigQuery's Translation API, with Gemini-powered error resolution."

root_agent = LlmAgent(
    name="oracle_to_bigquery",
    model="gemini-2.5-flash",
    description=AGENT_DESCRIPTION,
    instruction=AGENT_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2, top_p=0.95, max_output_tokens=65536
    ),
    tools=[
        run_sql_translation_tool,
        check_error_files_tool,
        analyze_sql_with_gemini_tool,
        resolve_sql_error_tool,
        upload_to_gcs_tool,
        mapping_tool,
    ],
)
