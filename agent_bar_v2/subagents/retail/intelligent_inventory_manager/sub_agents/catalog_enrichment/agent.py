# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Defining the Catalog Enrichment agent."""
from google.adk.agents import Agent
import os

from .prompts import SYSTEM_INSTRUCTIONS
from .tools import add_product_to_catalog, search_catalog

catalog_enrichment_agent = Agent(
    name="catalog_enrichment_agent",
    model=os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
    description="Agent to enrich retail product catalogs with missing details and descriptions.",
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[search_catalog, add_product_to_catalog],
)
