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
from pydantic import BaseModel

from .prompts import (SYSTEM_INSTRUCTION)
from .tools import (
    generate_build_plan_tool,
    summarize_build_plan_tool,
    execute_dynamic_graph_build,
    get_bq_dataset_schema,
    get_spanner_schema_core,
    query_spanner_graph_core,
)

from .config import (
    PROJECT_ID,
    PROJECT_LOCATION,
    BUCKET_NAME,
    BQ_DATASET_ID,
    SPANNER_INSTANCE,
    SPANNER_DATABASE,
    GRAPH_NAME,
)

# --- 2. Stateful Session Management ---
class SessionState(BaseModel):
    """A Pydantic model to represent the session state across turns."""

    build_plan: Any = None
    graph_store: Any = None
    retriever: Any = None


@lru_cache(maxsize=None)
def get_services():
    """Initializes and returns services, ensuring it only runs once."""
    vertexai.init(project=PROJECT_ID, location=PROJECT_LOCATION)

    state = SessionState()
    embeddings = VertexAIEmbeddings(
        model_name="text-embedding-005",
        project=PROJECT_ID,
        location=PROJECT_LOCATION,
    )
    return state, embeddings


# --- 3. Tool Preparation ---
TOOL_LIST = []


def _clean_json_string(json_string: str) -> str:
    """Removes markdown fences and leading/trailing whitespace from a JSON string."""
    if json_string.startswith("```json"):
        json_string = json_string[7:]
    if json_string.startswith("```"):
        json_string = json_string[3:]
    if json_string.endswith("```"):
        json_string = json_string[:-3]
    return json_string.strip()


def get_schema_wrapper() -> str:
    """Inspects the BigQuery dataset to get table schemas."""
    return get_bq_dataset_schema(project_id=PROJECT_ID, dataset_id=BQ_DATASET_ID)


def call_builder_tool_wrapper(user_request: str) -> str:
    """Generates a JSON build plan by calling the intelligent builder tool based on the user's request.
    Args:
        user_request: The natural language request from the user detailing what kind of graph they want to build (e.g., node types and relationships).
    """
    schema_json = get_schema_wrapper()
    plan_json = generate_build_plan_tool(
        user_request=user_request,
        schema_json=schema_json,
        project_id=PROJECT_ID,
        dataset_id=BQ_DATASET_ID,
        graph_name=GRAPH_NAME,
    )
    # Store it immediately so we don't have to pass huge JSON strings around
    session_state, _ = get_services()
    cleaned_json = _clean_json_string(plan_json)
    try:
        session_state.build_plan = json.loads(cleaned_json)
    except json.JSONDecodeError as e:
        return f"Failed to parse generated build plan: {e}. Raw output: {plan_json}"
    return "Build plan generated and saved to session state successfully."


def initialize_graph_services_wrapper() -> str:
    try:
        session_state, embedding_service = get_services()
        if not session_state.build_plan:
            return "Error: No build plan found in session state."
        plan = session_state.build_plan
        node_types = [node["node_type"] for node in plan.get("nodes", [])]
        if not node_types:
            return "Error: Build plan contains no node types to index."
        session_state.graph_store = SpannerGraphStore(
            instance_id=SPANNER_INSTANCE,
            database_id=SPANNER_DATABASE,
            graph_name=GRAPH_NAME,
        )
        session_state.retriever = SpannerGraphVectorContextRetriever.from_params(
            graph_store=session_state.graph_store,
            embedding_service=embedding_service,
            llm=ChatVertexAI(
                model="gemini-2.5-flash",
                project=PROJECT_ID,
                location=PROJECT_LOCATION,
            ),
            expand_by_hops=2,
        )
        return "Successfully initialized graph services."
    except Exception as e:
        return f"Error during service initialization: {e}"


def execute_build_wrapper(cleanup_graph: bool = False) -> str:
    """Executes the stored JSON build plan to create the graph AND generate embeddings."""
    session_state, embedding_service = get_services()
    if not session_state.graph_store:
        return "Error: Graph services must be initialized first."
    if not session_state.build_plan:
        return "Error: No build plan found in session state."

    # Serialize it back to pass to the dynamic execution tool
    plan_json_str = json.dumps(session_state.build_plan)
    return execute_dynamic_graph_build(
        project_id=PROJECT_ID,
        graph_store=session_state.graph_store,
        build_plan_json=plan_json_str,
        embedding_service=embedding_service,
        cleanup_first=cleanup_graph,
    )


def _is_safe_cypher_query(query: str) -> bool:
    """
    Validates that the Cypher query does not contain destructive keywords.
    """
    # List of keywords that modify or delete data
    disallowed_keywords = ["DELETE", "DETACH", "CREATE", "SET", "REMOVE", "MERGE"]
    query_upper = query.upper()
    for keyword in disallowed_keywords:
        if keyword in query_upper:
            return False
    return True


# ** NEW, SIMPLER QUERY TOOLS **
def execute_direct_traversal(tool_name: str, parameters_json: str) -> str:
    """Executes a specific, predefined traversal query. Use this for simple, direct lookups."""
    session_state, embedding_service = get_services()
    if not session_state.graph_store or not session_state.build_plan:
        return "Error: Services not initialized or build plan not found."
    try:
        params = json.loads(parameters_json)
        query_template = session_state.build_plan["traversal_tools"].get(tool_name)
        if not query_template:
            return f"Error: Direct traversal tool '{tool_name}' not found in the build plan."
        if not _is_safe_cypher_query(query_template):
            return (
                "Error: Malicious or invalid Cypher query detected. Execution halted."
            )
        query_to_run = query_template.format(graph_name=GRAPH_NAME)
        results = session_state.graph_store.query(query_to_run, params=params)
        return json.dumps(results, indent=2) if results else "No results found."
    except Exception as e:
        return f"Error executing direct traversal: {e}"


def answer_question_with_graph_rag(natural_language_query: str) -> str:
    """Answers complex or vague questions using the powerful GraphRAG retriever."""
    session_state, embedding_service = get_services()
    if not session_state.retriever:
        return "Error: Graph retriever not available. Please build the graph first."
    try:
        result_documents = session_state.retriever.invoke(natural_language_query)
        formatted_results = [json.loads(doc.page_content) for doc in result_documents]
        return json.dumps(formatted_results, indent=2)
    except Exception as e:
        return f"Error during GraphRAG query: {e}"


def summarize_build_plan_wrapper() -> str:
    """Generates a human-readable summary of the stored JSON build plan."""
    session_state, _ = get_services()
    if not session_state.build_plan:
        return "Error: No build plan found in session state to summarize."
    plan_json_str = json.dumps(session_state.build_plan)
    return summarize_build_plan_tool(build_plan_json=plan_json_str)


# ** NEW SPANNER QA TOOLS **
def get_spanner_schema_wrapper() -> str:
    """
    Retrieves the schema of the Spanner Graph, including node labels and properties.
    Use this to understand what data maps to which properties (e.g. is it 'Active' or 'active'?).
    """
    session_state, _ = get_services()
    if not session_state.graph_store:
        # Initialize graph store if not already done, just to get schema
        session_state.graph_store = SpannerGraphStore(
            instance_id=SPANNER_INSTANCE,
            database_id=SPANNER_DATABASE,
            graph_name=GRAPH_NAME,
        )
    return get_spanner_schema_core(session_state.graph_store)


def query_spanner_graph_wrapper(question: str) -> str:
    """
    Answers a question by querying the Spanner Graph generating GQL automatically.
    Returns the answer and the GQL query used.
    """
    session_state, _ = get_services()
    if not session_state.graph_store:
        # Initialize graph store if not already done
        session_state.graph_store = SpannerGraphStore(
            instance_id=SPANNER_INSTANCE,
            database_id=SPANNER_DATABASE,
            graph_name=GRAPH_NAME,
        )
    return query_spanner_graph_core(question, session_state.graph_store)


TOOL_LIST = [
    get_schema_wrapper,
    call_builder_tool_wrapper,
    summarize_build_plan_wrapper,
    initialize_graph_services_wrapper,
    execute_build_wrapper,
    execute_direct_traversal,  # New direct tool
    answer_question_with_graph_rag,  # New retriever tool
    get_spanner_schema_wrapper,  # New spanner schema tool
    query_spanner_graph_wrapper,  # New spanner QA tool
]

# --- 4. Root Agent Definition ---
root_agent = Agent(
    name="Graph_Orchestrator_Agent",
    model="gemini-2.5-flash",
    description="A master agent that orchestrates intelligent tools to build and query knowledge graphs.",
    instruction=SYSTEM_INSTRUCTION,
    tools=TOOL_LIST,
)