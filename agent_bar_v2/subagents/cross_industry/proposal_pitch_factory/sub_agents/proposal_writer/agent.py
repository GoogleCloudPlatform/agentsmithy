from google.adk.agents import LlmAgent
from google.adk.tools import load_artifacts
from google.genai import types
from .prompt import AGENT_INSTRUCTION, AGENT_DESCRIPTION


AGENT_ID = "proposal_drafter_agent"

AGENT_MODEL = "gemini-2.5-pro"

def load_agent() -> LlmAgent:
    agent = LlmAgent(
        model=AGENT_MODEL,
        generate_content_config=types.GenerateContentConfig(
            temperature=0.6, top_p=0.95, max_output_tokens=65535
        ),
        name=AGENT_ID,
        description=AGENT_DESCRIPTION,
        instruction=AGENT_INSTRUCTION,
        tools=[load_artifacts],
    )
    return agent


root_agent = load_agent()