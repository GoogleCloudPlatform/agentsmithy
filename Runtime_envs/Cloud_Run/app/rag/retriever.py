# Copyright 2025 Google LLC
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

import os
from unittest.mock import MagicMock

from langchain_google_community import VertexAISearchRetriever
from langchain_google_community.vertex_rank import VertexAIRank
from langchain_google_vertexai import VertexAIEmbeddings


def get_retriever(
    project_id: str,
    data_store_id: str,
    agent_builder_location: str,
) -> VertexAISearchRetriever:
    """
    Creates and returns an instance of the retriever service.

    Uses mock service if the INTEGRATION_TEST environment variable is set to "TRUE",
    otherwise initializes real Vertex AI retriever.
    """
    if os.getenv("INTEGRATION_TEST") == "TRUE":
        retriever = MagicMock()
        retriever.invoke = lambda x: []
        return retriever

    return VertexAISearchRetriever(
        project_id=project_id,
        data_store_id=data_store_id,
        location_id=agent_builder_location,
        engine_data_type=0,
    )


def get_compressor(project_id: str) -> VertexAIRank:
    """
    Creates and returns an instance of the compressor service.

    Uses mock service if the INTEGRATION_TEST environment variable is set to "TRUE",
    otherwise initializes real Vertex AI compressor.
    """
    if os.getenv("INTEGRATION_TEST") == "TRUE":
        compressor = MagicMock()
        compressor.compress_documents = lambda documents, query: []
        return compressor

    return VertexAIRank(
        project_id=project_id,
        location_id="global",
        ranking_config="default_ranking_config",
        title_field="id",
        top_n=5,
    )
