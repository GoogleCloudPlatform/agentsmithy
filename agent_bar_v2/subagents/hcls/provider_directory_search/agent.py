"""Provider Directory Search agent definition."""

from google.adk.agents import Agent

from .prompt import PROVIDER_DIRECTORY_SEARCH_PROMPT
from .tools import PROVIDER_SEARCH_TOOLS

root_agent = Agent(
    model="gemini-2.0-flash",
    name="provider_directory_search",
    description=(
        "Helps users search for healthcare practitioners, facilities, and "
        "organizations by name, specialty, location, or relationship."
    ),
    instruction=PROVIDER_DIRECTORY_SEARCH_PROMPT,
    tools=PROVIDER_SEARCH_TOOLS,
)
