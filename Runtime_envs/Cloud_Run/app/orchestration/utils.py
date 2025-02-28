# ==============================================================================
# Copyright 2025 Google LLC. This software is provided as-is, without warranty
# or representation for any use or purpose. Your use of it is subject to your
# agreement with Google.
# ==============================================================================
"""Module that contains various utility functions."""

from langchain_core.prompts import ChatPromptTemplate

from app.orchestration.constants import (
    FINANCE_AGENT_DESCRIPTION,
    HEALTHCARE_AGENT_DESCRIPTION,
    RETAIL_AGENT_DESCRIPTION,
    DEFAULT_AGENT_DESCRIPTION
)
from app.orchestration.enums import IndustryType


def get_init_prompt(industry_type: str) -> ChatPromptTemplate:
    """Creates the initialization prompt for the agent based on the industry."""

    if industry_type == IndustryType.FINANCE_INDUSTRY.value:
        sys_desc = FINANCE_AGENT_DESCRIPTION
    elif industry_type == IndustryType.HEALTHCARE_INDUSTRY.value:
        sys_desc = HEALTHCARE_AGENT_DESCRIPTION
    elif industry_type == IndustryType.RETAIL_INDUSTRY.value:
        sys_desc = RETAIL_AGENT_DESCRIPTION
    else:
        sys_desc = DEFAULT_AGENT_DESCRIPTION

    return ChatPromptTemplate.from_messages([
        ("system", f"{sys_desc}"),
        ("placeholder", "{messages}")
    ])
