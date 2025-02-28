# ==============================================================================
# Copyright 2025 Google LLC. This software is provided as-is, without warranty
# or representation for any use or purpose. Your use of it is subject to your
# agreement with Google.
# ==============================================================================

from enum import Enum

class OrchestrationFramework(Enum):
    """Enum representing the available agent orchestration framework options."""

    LANGCHAIN_REACT_AGENT = 'langchain_react_agent'
    LANGGRAPH_AGENT = 'langgraph_agent'
    LLAMA_AGENT = 'llama_agent'
    VERTEX_AI_REASONING_ENGINE_LANCHAIN_AGENT = 'vertex_ai_reasoning_engine_langchain_agent'
    # VERTEX_AI_AGENT_FRAMEWORK_AGENT = 'vertex_ai_agent_framework_agent' # Future

class IndustryType(Enum):
    """Enum representing the available Langchain agent options."""

    FINANCE_INDUSTRY = 'finance'
    RETAIL_INDUSTRY = 'retail'
    HEALTHCARE_INDUSTRY = 'healthcare'
