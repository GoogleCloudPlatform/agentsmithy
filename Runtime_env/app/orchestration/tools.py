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
# pylint: disable=C0301, R1714
"""Module that contains various tool definitions."""
from typing import List

from google.adk.tools import VertexAiSearchTool

from langchain_core.documents import Document
from langchain_core.tools import StructuredTool
from langchain_community.tools.pubmed.tool import PubmedQueryRun
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from langchain_community.tools.google_scholar import GoogleScholarQueryRun
from langchain_community.tools.google_trends import GoogleTrendsQueryRun
from langchain_community.tools.google_finance import GoogleFinanceQueryRun
from langchain_community.utilities.google_scholar import GoogleScholarAPIWrapper
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.google_trends import GoogleTrendsAPIWrapper
from langchain_community.utilities.google_finance import GoogleFinanceAPIWrapper
import vertexai

# LlamaIndex
from llama_index.core.tools import FunctionTool
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.retrievers.vertexai_search import VertexAISearchRetriever

from app.orchestration.config import (
    PROJECT_ID,
    AGENT_BUILDER_LOCATION,
    DATA_STORE_ID,
    SERP_API_KEY
)
from app.orchestration.enums import (
    IndustryType,
    OrchestrationFramework
)
from app.rag.templates import format_docs
from app.rag.retriever import get_compressor, get_retriever


# Initialize Vertex AI
vertexai.init(project=PROJECT_ID)


### langchain/langgraph tools: ###

lang_retriever = get_retriever(
    project_id=PROJECT_ID,
    data_store_id=DATA_STORE_ID,
    agent_builder_location=AGENT_BUILDER_LOCATION,
)
compressor = get_compressor(project_id=PROJECT_ID)


def retrieve_info(query: str) -> tuple[str, List[Document]]:
    """
    Use this when you need additional information to answer a question.
    Useful for retrieving relevant information based on a query.

    Available documents:
       Finance: `Alphabet Investor PDFs`: This data contains quarterly earnings releases
        and annual reports for Alphabet for every quarter since 2004. The Annual reports include 
        financial statements (balance sheet, income statement, cash flow statement), a letter to
        shareholders, management discussion and analysis (MD&A), and information on corporate governance.
        The quarterly earnings releases also contain key financial statements like the income statement,
        balance sheet, and cash flow statement, along with management commentary and analysis of
        quarterly performance.
        Dataset can be found here:
        https://console.cloud.google.com/storage/browser/cloud-samples-data/gen-app-builder/search/alphabet-investor-pdfs

       HealthCare: `PriMock57 Healthcare consultations`: This dataset consists of 57
        mock medical primary care consultations held over 5 days by 7
        Babylon clinicians and 57 Babylon employees acting as patients,
        using case cards with presenting complaints, symptoms, medical
        & general history etc.
        Dataset can be found here:
        https://console.cloud.google.com/storage/browser/cloud-samples-data/vertex-ai/medlm/primock57/transcripts

      Retail: `Google Store`: This data is a list of html web pages from the Google Store from
        2023. It represents a listing of products, details, prices, etc related to
        Google products.
        Dataset can be found here:
        https://console.cloud.google.com/storage/browser/cloud-samples-data/dialogflow-cx/google-store

    Args:
        query (str): The user's question or search query.

    Returns:
        List[Document]: A list of the top-ranked Document objects, limited to TOP_K (5) results.
    """
    # Use the retriever to fetch relevant documents based on the query
    retrieved_docs = lang_retriever.invoke(query)
    # Re-rank docs with Vertex AI Rank for better relevance
    ranked_docs = compressor.compress_documents(documents=retrieved_docs, query=query)
    # Format ranked documents into a consistent structure for LLM consumption
    formatted_docs = format_docs.format(docs=ranked_docs)
    return (formatted_docs, ranked_docs)


def google_search_tool(query: str) -> str:
    """Uses Google Search to gather information from the internet."""
    search = GoogleSerperAPIWrapper()
    return search.run(query)


def google_scholar_tool(query: str) -> str:
    """Uses Google Scholar to answer complex technical questions."""
    google_scholar = GoogleScholarQueryRun(api_wrapper=GoogleScholarAPIWrapper())
    return google_scholar.invoke(query)


def google_trends_tool(query: str) -> str:
    """Uses Google Trends to get information on trending search results and news."""
    google_trends = GoogleTrendsQueryRun(api_wrapper=GoogleTrendsAPIWrapper())
    return google_trends.invoke(query)


def google_finance_tool(query: str) -> str:
    """Uses Google Finance to get information from the Google Finance page."""
    google_finance = GoogleFinanceQueryRun(api_wrapper=GoogleFinanceAPIWrapper())
    return google_finance.invoke(query)


def yahoo_finance_tool(query: str) -> str:
    """Uses Yahoo Finance to get real-time new and information on financial markets."""
    yahoo_finance = YahooFinanceNewsTool()
    return yahoo_finance.invoke(query)


def medical_publications_tool(query: str) -> str:
    """Use this tool if the user asks very complicated medical questions
        that can only be answered by searching through medical publications
        and journals.
    """
    pubmed = PubmedQueryRun()
    return pubmed.invoke(query)


def should_continue() -> None:
    """
    Use this tool if you determine that you have enough context to respond to the questions of the user.
    """
    return None


def get_tools(
        industry_type: str,
        orchestration_framework: str
    ) -> list:
    """Grabs a list of tools based on the user's configselection"""

    tools_list = []
    # if industry_type == IndustryType.FINANCE_INDUSTRY.value:
    #     tools_list.append(yahoo_finance_tool)
    if industry_type == IndustryType.HEALTHCARE_INDUSTRY.value:
        tools_list.append(medical_publications_tool)
    # elif industry_type == IndustryType.RETAIL_INDUSTRY.value:
    #     tools_list.append(retail_discovery_tool)

    # These tools are only used if the user specifies a SERPER_API_KEY
    if SERP_API_KEY != "unset":
        tools_list.extend([
            google_search_tool,
            google_scholar_tool,
            google_trends_tool,
            google_finance_tool
        ])
    # The Vertex AI Search Tool is only used if the user specifies a DATA_STORE_ID
    if DATA_STORE_ID != "unset" and orchestration_framework != OrchestrationFramework.VERTEX_AI_AGENT_FRAMEWORK_AGENT.value:
        tools_list.append(retrieve_info)

    # ADK agent currently does not support multiple tool including ADK built-in tool
    if orchestration_framework != OrchestrationFramework.VERTEX_AI_AGENT_FRAMEWORK_AGENT.value:
        tools_list.extend([
            # fallback,
            should_continue
        ])

    # If using langchain or langgraph, then the tools must be defined as structured tools
    if (orchestration_framework == OrchestrationFramework.LANGCHAIN_PREBUILT_AGENT.value or
        orchestration_framework == OrchestrationFramework.LANGGRAPH_PREBUILT_AGENT.value):
        tools_list = [StructuredTool.from_function(tool) for tool in tools_list]

    elif orchestration_framework == OrchestrationFramework.VERTEX_AI_AGENT_FRAMEWORK_AGENT.value:
        if DATA_STORE_ID != "unset":
            vais_tool = VertexAiSearchTool(
                data_store_id=f"projects/{PROJECT_ID}/locations/{AGENT_BUILDER_LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}"
            )
            vais_tool.name = "Vertex AI Search"
            vais_tool.description = (
                "Use this when you need additional information to answer a "
                "question. Useful for retrieving relevant information based on "
                "a query.")

            # ADK agent currently only support one built-in tool
            # see https://google.github.io/adk-docs/tools/built-in-tools/#limitations
            tools_list = [vais_tool]

    return tools_list

### llamaindex tools: ###

llama_retriever = VertexAISearchRetriever(
    project_id=PROJECT_ID,
    data_store_id=DATA_STORE_ID,
    location_id=AGENT_BUILDER_LOCATION,
    engine_data_type=0,
)

def llamaindex_query_engine_tool(query: str) -> str:
    """
    Use this when you need additional information to answer a question.
    Useful for retrieving relevant information based on a query.

    Available documents:
       Finance: `Alphabet Investor PDFs`: This data contains quarterly earnings releases
        and annual reports for Alphabet for every quarter since 2004. The Annual reports include 
        financial statements (balance sheet, income statement, cash flow statement), a letter to
        shareholders, management discussion and analysis (MD&A), and information on corporate governance.
        The quarterly earnings releases also contain key financial statements like the income statement,
        balance sheet, and cash flow statement, along with management commentary and analysis of
        quarterly performance.
        Dataset can be found here:
        https://console.cloud.google.com/storage/browser/cloud-samples-data/gen-app-builder/search/alphabet-investor-pdfs

       HealthCare: `PriMock57 Healthcare consultations`: This dataset consists of 57
        mock medical primary care consultations held over 5 days by 7
        Babylon clinicians and 57 Babylon employees acting as patients,
        using case cards with presenting complaints, symptoms, medical
        & general history etc.
        Dataset can be found here:
        https://console.cloud.google.com/storage/browser/cloud-samples-data/vertex-ai/medlm/primock57/transcripts

      Retail: `Google Store`: This data is a list of html web pages from the Google Store from
        2023. It represents a listing of products, details, prices, etc related to
        Google products.
        Dataset can be found here:
        https://console.cloud.google.com/storage/browser/cloud-samples-data/dialogflow-cx/google-store

    Args:
        query (str): The user's question or search query.

    Returns:
        List[Document]: A list of the top-ranked Document objects
    """
    query_engine = RetrieverQueryEngine.from_args(llama_retriever)
    response = query_engine.query(query)
    return str(response)


def get_llamaindex_tools(industry_type: str = None) -> list:
    """Grabs a list of tools based on the user's configselection"""

    tools_list = []
    # if industry_type == IndustryType.FINANCE_INDUSTRY.value:
    #     tool_spec = YahooFinanceToolSpec()
    #     tools_list.extend(tool_spec.to_tool_list())
    if industry_type == IndustryType.HEALTHCARE_INDUSTRY.value:
        tools_list.append(FunctionTool.from_defaults(fn=medical_publications_tool))
    # elif industry_type == IndustryType.RETAIL_INDUSTRY.value:
    #     tools_list.append(retail_discovery_tool)

    # These tools are only used if the user specifies a SERPER_API_KEY
    if SERP_API_KEY != "unset":
        tools_list.extend([
            FunctionTool.from_defaults(fn=google_search_tool),
            FunctionTool.from_defaults(fn=google_scholar_tool),
            FunctionTool.from_defaults(fn=google_trends_tool),
            FunctionTool.from_defaults(fn=google_finance_tool)
        ])

    if DATA_STORE_ID != "unset":
        tools_list.append(FunctionTool.from_defaults(fn=llamaindex_query_engine_tool))

    return tools_list
