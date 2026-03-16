# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
from functools import lru_cache
from typing import Any

import vertexai
from google.adk.agents import Agent
from langchain_google_spanner import SpannerGraphStore
from langchain_google_spanner.graph_retriever import SpannerGraphVectorContextRetriever
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

from .prompts import (SYSTEM_INSTRUCTION)
from . import tools


# --- 4. Root Agent Definition ---
root_agent = Agent(
    name="Graph_Orchestrator_Agent",
    model="gemini-2.5-flash",
    description="A master agent that orchestrates intelligent tools to build and query knowledge graphs.",
    instruction=SYSTEM_INSTRUCTION,
    tools=tools.tools,
)