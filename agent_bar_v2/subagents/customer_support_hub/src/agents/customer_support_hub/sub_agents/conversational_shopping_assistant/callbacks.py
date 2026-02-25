"""Defines agent lifecycle callbacks"""

import copy
import html
import os
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.genai import types

MAX_CITATIONS = int(os.getenv("MAX_CITATIONS", 4))


def build_citation_link(chunk: types.GroundingChunk) -> str:
    """Builds html <a> tag for citation source"""

    link = ""
    retrieved_context = chunk.retrieved_context

    if retrieved_context:
        uri = retrieved_context.uri
        title = retrieved_context.title
        if uri and title:
            uri = uri.replace("gs://", "")
            uri = html.escape(uri)
            title = html.escape(title)
            href = f"https://storage.mtls.cloud.google.com/{uri}"
            link = (
                f'\n- <a href="{href}" target="_blank" rel="noopener noreferrer">'
                f"{title}</a>"
            )
    return link


def add_citations_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    Appends grounding sources and links to the end of the LLM response.
    If grounding metadata is available, it returns the modified response.
    If grounding metadata is None, it returns the original response.
    """

    new_response = None

    if llm_response.grounding_metadata:
        metadata = llm_response.grounding_metadata

        citations = "\n\nSources:"
        if metadata.grounding_chunks:
            for chunk in metadata.grounding_chunks[:MAX_CITATIONS]:
                citations += build_citation_link(chunk)

            content = llm_response.content
            if content:
                parts = content.parts
                if parts:
                    modified_parts = [copy.deepcopy(part) for part in parts]
                    modified_parts[0].text = f"{parts[0].text} {citations}"

                    new_response = LlmResponse(
                        content=types.Content(role="model", parts=modified_parts),
                        grounding_metadata=None,
                    )

    setattr(llm_response, "grounding_metadata", None)
    return new_response
