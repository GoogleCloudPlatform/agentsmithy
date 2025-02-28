# ==============================================================================
# Copyright 2025 Google LLC. This software is provided as-is, without warranty
# or representation for any use or purpose. Your use of it is subject to your
# agreement with Google.
# ==============================================================================

"""Module that contains various tool definitions."""
from typing import List

# from ionic_langchain.tool import IonicTool
from langchain_core.documents import Document
from langchain_core.tools import tool
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

from app.orchestration.config import (
    PROJECT_ID,
    AGENT_BUILDER_LOCATION,
    DATA_STORE_ID,
    SERP_API_KEY
)
from app.orchestration.enums import IndustryType
from app.orchestration.models import gemini_20_chat_llm
from app.rag.templates import format_docs
from app.rag.retriever import get_compressor, get_retriever


# Initialize Vertex AI
vertexai.init(project=PROJECT_ID)

retriever = get_retriever(
    project_id=PROJECT_ID,
    data_store_id=DATA_STORE_ID,
    agent_builder_location=AGENT_BUILDER_LOCATION,
)
compressor = get_compressor(project_id=PROJECT_ID)

@tool(response_format="content_and_artifact")
def retrieve_info(query: str) -> tuple[str, List[Document]]:
    """
    Try this tool first.
    Use this when you need additional information to answer a question.
    Useful for retrieving relevant documents based on a query.

    Available documents:
       Finance: `investments_data`: This data contains structured data about various
        investment options, including ETFs and individual stocks. Each entry provides
        key information like ticker symbol, market, investment rating, a textual
        overview, and an investment analysis. This data facilitates quantitative and
        qualitative investment research and analysis, potentially enabling automated
        insights generation.
       HealthCare: `PriMock57 Healthcare consultations`: This dataset consists of 57
        mock medical primary care consultations held over 5 days by 7
        Babylon clinicians and 57 Babylon employees acting as patients,
        using case cards with presenting complaints, symptoms, medical
        & general history etc.
      Retail: `Google Store`: This data is a list of pages from the Google Store from
        2023. It represents a listing of products, details, prices, etc related to
        Google products.

      TODO
      Retail: `Toy Products`: This dataset provides a comprehensive listing of a toy
        product catalog. Each row represents a unique product with attributes like
        name, manufacturer, price, description, and product information.

    Args:
        query (str): The user's question or search query.

    Returns:
        List[Document]: A list of the top-ranked Document objects, limited to TOP_K (5) results.
    """
    # Use the retriever to fetch relevant documents based on the query
    retrieved_docs = retriever.invoke(query)
    # Re-rank docs with Vertex AI Rank for better relevance
    ranked_docs = compressor.compress_documents(documents=retrieved_docs, query=query)
    # Format ranked documents into a consistent structure for LLM consumption
    formatted_docs = format_docs.format(docs=ranked_docs)
    return (formatted_docs, ranked_docs)

@tool
def google_search_tool(query: str) -> str:
    """Uses Google Search to gather information from the internet."""
    search = GoogleSerperAPIWrapper()
    return search.run(query)

@tool
def google_scholar_tool(query: str) -> str:
    """Uses Google Scholar to answer complex technical questions."""
    google_scholar = GoogleScholarQueryRun(api_wrapper=GoogleScholarAPIWrapper())
    return google_scholar.invoke(query)

@tool
def google_trends_tool(query: str) -> str:
    """Uses Google Trends to get information on trending search results and news."""
    google_trends = GoogleTrendsQueryRun(api_wrapper=GoogleTrendsAPIWrapper())
    return google_trends.invoke(query)

@tool
def google_finance_tool(query: str) -> str:
    """Uses Google Finance to get information from the Google Finance page."""
    google_finance = GoogleFinanceQueryRun(api_wrapper=GoogleFinanceAPIWrapper())
    return google_finance.invoke(query)

# @tool
# def yahoo_finance_tool(query: str) -> str:
#     """Uses Yahoo Finance to get real-time new and information on financial markets."""
#     yahoo_finance = YahooFinanceNewsTool()
#     print(query)
#     stop

    # prompt = f"""You are a helpful assistant who retrieves finance news. Based on
    #             the users query, I would like you to pull out the stock ticker of
    #             the company that the user is referencing. Respond with only the
    #             stock ticker. If not company is mentioned, say "No company".
    #             User query: {query}"""
    # stock_ticker = gemini_20_chat_llm.invoke(prompt)
    # print("stock_ticker:", stock_ticker)

    # try:
    #     response = yahoo_finance.invoke({"query": stock_ticker})
    # except Exception as e:
    #     new_prompt = f"{prompt}; correct for this error: {str(e)}"
    #     stock_ticker = gemini_20_chat_llm.invoke(new_prompt)
    #     print("new stock_ticker:", {"query": stock_ticker})
    #     response = yahoo_finance.invoke(stock_ticker)
    # return response

@tool
def medical_publications_tool(query: str) -> str:
    """Use this tool if the user asks very complicated medical questions
        that can only be answered by searching through medical publications
        and journals.
    """
    pubmed = PubmedQueryRun()
    return pubmed.invoke(query)

# `pip install ionic-langchain``
# @tool
# def retail_discovery_tool(query: str) -> str:
#     """Ionic is an e-commerce shopping tool. Use this tool when the user is looking
#         for a product recommendation or trying to find a specific product.

#         Example question: I'm looking for a new 4k monitor can you find me some options
#         for less than $1000
#     """
#     ionic = IonicTool()
#     return ionic.tool().invoke(query)

@tool
def should_continue() -> None:
    """
    Use this tool if you determine that you have enough context to respond to the questions of the user.
    """
    return None

def fallback(query: str) -> str:
    """
    Only use this tool if you have tried other tools and still do not have enough context to respond to 
    the questions of the user.
    This tool will attempt to answer the question using Google Gemini.
    """
    response = gemini_20_chat_llm.stream(query)
    return response

def get_tools(industry_type: str = None) -> list:
    """Grabs a list of tools based on the user's configselection"""

    tools_list = []
    if industry_type == IndustryType.FINANCE_INDUSTRY.value:
        tools_list.append(YahooFinanceNewsTool())
    elif industry_type == IndustryType.HEALTHCARE_INDUSTRY.value:
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
    if DATA_STORE_ID != "unset":
        tools_list.append(retrieve_info)

    tools_list.extend([
        # fallback,
        should_continue
    ])
    return tools_list
