# Copyright 2025 Google LLC. All Rights Reserved.
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
# pylint: disable=C0301
"""Defines list of supported orchestration frameworks and industries"""
from enum import Enum

class OrchestrationFramework(Enum):
    """Enum representing the available agent orchestration framework options."""

    LANGCHAIN_PREBUILT_AGENT = 'langchain_prebuilt_agent'
    LANGCHAIN_VERTEX_AI_AGENT_ENGINE_AGENT = 'langchain_vertex_ai_agent_engine_agent'
    LANGGRAPH_PREBUILT_AGENT = 'langgraph_prebuilt_agent'
    # LANGGRAPH_CUSTOM_AGENT = 'langgraph_custom_agent' # Coming Soon
    LANGGRAPH_VERTEX_AI_AGENT_ENGINE_AGENT = 'langgraph_vertex_ai_agent_engine_agent'
    LLAMAINDEX_AGENT = 'llamaindex_agent'
    # CREW_AI_AGENT = 'crew_ai_agent' # Coming Soon
    VERTEX_AI_AGENT_FRAMEWORK_AGENT = 'vertex_ai_agent_framework_agent'

class IndustryType(Enum):
    """Enum representing the available Langchain agent options."""

    FINANCE_INDUSTRY = 'finance'
    RETAIL_INDUSTRY = 'retail'
    HEALTHCARE_INDUSTRY = 'healthcare'
