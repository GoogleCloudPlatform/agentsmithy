"""Defines Retail Concierge agent"""

import os

from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool

from .callbacks import add_citations_callback
from .prompt import SYSTEM_INSTRUCTIONS

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
DATASTORE_ID = os.getenv("DATASTORE_ID")
DATASTORE_REF = os.path.join(
    f"projects/{PROJECT_ID}/locations/global/collections/",
    f"default_collection/dataStores/{DATASTORE_ID}",
)


def load_agent(name: str) -> LlmAgent:
    """Load an agent instance.

    Args:
        name: Name of the agent to create.

    Returns:
        An agent instance.
    """

    agent = LlmAgent(
        name=name,
        model="gemini-2.5-flash",
        instruction=SYSTEM_INSTRUCTIONS,
        tools=[VertexAiSearchTool(data_store_id=DATASTORE_REF)],
        after_model_callback=add_citations_callback,
    )

    return agent


root_agent = load_agent("conversational_shopping_assistant")
