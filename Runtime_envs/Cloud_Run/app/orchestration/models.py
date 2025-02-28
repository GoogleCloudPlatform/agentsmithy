# ==============================================================================
# Copyright 2025 Google LLC. This software is provided as-is, without warranty
# or representation for any use or purpose. Your use of it is subject to your
# agreement with Google.
# ==============================================================================

"""Module that defines default LLM configurations for the Langchain Agent."""

from langchain_google_vertexai import ChatVertexAI

from app.orchestration.constants import (
    GEMINI_FLASH_20_LATEST,
    GEMINI_PRO_15_LATEST
)

gemini_20_chat_llm = ChatVertexAI(
    model_name=GEMINI_FLASH_20_LATEST,
    temperature=0,
    top_p=1.0,
    top_k=1
)

gemini_15_chat_llm = ChatVertexAI(
    model_name=GEMINI_PRO_15_LATEST,
    temperature=0,
    top_p=1.0,
    top_k=1
)

def get_model_obj_from_string(model_name: str):
    if model_name == GEMINI_FLASH_20_LATEST:
        return gemini_20_chat_llm
    elif model_name == GEMINI_PRO_15_LATEST:
        return gemini_15_chat_llm
    else:
        raise ValueError(f'Model Name {model_name} is not currently supported.')
