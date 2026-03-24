import os
"""Defining the Catalog Enrichment agent."""
from google.adk.agents import Agent

from .prompts import SYSTEM_INSTRUCTIONS
from .tools import add_product_to_catalog, search_catalog

catalog_enrichment_agent = Agent(
    name="catalog_enrichment",
    model=os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview"),
    description="Agent to enrich retail product catalogs with missing details and descriptions.",
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[search_catalog, add_product_to_catalog],
)
