# Copyright 2026 Google LLC. All Rights Reserved.
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
