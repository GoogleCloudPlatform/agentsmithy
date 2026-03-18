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
from typing import Any, Optional
import logging
from pydantic import BaseModel

import sqlparse
from google.cloud import bigquery
from langchain_community.graphs.graph_document import (
    GraphDocument,
    Node,
    Relationship,
)
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_spanner import SpannerGraphStore, SpannerGraphQAChain, SpannerGraphStore
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

from .config import (
    PROJECT_ID,
    PROJECT_LOCATION,
    BUCKET_NAME,
    BQ_DATASET_ID,
    SPANNER_INSTANCE,
    SPANNER_DATABASE,
    GRAPH_NAME,
)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
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

# dynamic graph tools
def get_bq_dataset_schema(project_id: str, dataset_id: str) -> str:
    """
    Inspects all tables in a BigQuery dataset and returns their schemas,
    including PRIMARY KEY and FOREIGN KEY constraints, as a JSON string.
    """
    try:
        client = bigquery.Client(project=project_id)

        # 1. Fetch raw table columns
        tables = client.list_tables(f"{project_id}.{dataset_id}")
        schema_info = {}
        for table_item in tables:
            table = client.get_table(table_item)
            schema_info[table.table_id] = {
                "columns": [f"{f.name} ({f.field_type})" for f in table.schema],
                "primary_keys": [],
                "foreign_keys": [],
            }

        # 2. Fetch constraints (PKs and FKs)
        query = f"""
        SELECT
            tc.table_name,
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name,
            ccu.table_name AS referenced_table_name,
            ccu.column_name AS referenced_column_name
        FROM
            `{project_id}.{dataset_id}.INFORMATION_SCHEMA.TABLE_CONSTRAINTS` tc
        LEFT JOIN
            `{project_id}.{dataset_id}.INFORMATION_SCHEMA.KEY_COLUMN_USAGE` kcu
            ON tc.constraint_name = kcu.constraint_name
        LEFT JOIN
            `{project_id}.{dataset_id}.INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE` ccu
            ON tc.constraint_name = ccu.constraint_name
        WHERE
            tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY')
        """
        try:
            results = client.query(query).result()
            for row in results:
                table_name = row["table_name"]
                if table_name not in schema_info:
                    continue

                if row["constraint_type"] == "PRIMARY KEY":
                    if (
                        row["column_name"]
                        and row["column_name"]
                        not in schema_info[table_name]["primary_keys"]
                    ):
                        schema_info[table_name]["primary_keys"].append(
                            row["column_name"]
                        )
                elif row["constraint_type"] == "FOREIGN KEY":
                    fk_entry = {
                        "column": row["column_name"],
                        "referenced_table": row["referenced_table_name"],
                        "referenced_column": row["referenced_column_name"],
                    }
                    if fk_entry not in schema_info[table_name]["foreign_keys"]:
                        schema_info[table_name]["foreign_keys"].append(fk_entry)
        except Exception as query_e:
            logging.warning(f"Could not fetch constraints: {query_e}")

        return json.dumps(schema_info, indent=2) if schema_info else "No tables found."
    except Exception as e:
        return f"Error inspecting BigQuery dataset: {e}"


def is_safe_bq_query(query: str) -> bool:
    """Validates that the query is a single, read-only SELECT statement."""
    parsed = sqlparse.parse(query)

    try:
        # If the query is empty/invalid, parsed will be empty,
        # and parsed[0] will raise an IndexError.
        statement = parsed[0]

        # Deny multi-statement queries and non-SELECT queries
        if len(parsed) > 1 or statement.get_type() != "SELECT":
            return False

        return True

    except IndexError:
        # If we get an IndexError, it's an invalid query, so we fail safely.
        return False


def execute_dynamic_graph_build(
    project_id: str,
    graph_store: SpannerGraphStore,
    build_plan_json: str,
    embedding_service: VertexAIEmbeddings,  # Add embedding_service as an argument
    cleanup_first: bool = False,
) -> str:
    """
    Executes the graph build process, now including explicit embedding generation.
    """
    logging.info("TOOL: Executing Dynamic Graph Build")
    try:
        plan = json.loads(build_plan_json)

        bq_query = plan["bq_etl_query"]
        if not is_safe_bq_query(bq_query):
            logging.error(f"Generated BigQuery query failed validation: {bq_query}")
            return (
                "Error: Malicious or invalid BigQuery query detected. Execution halted."
            )

        client = bigquery.Client(project=project_id)

        rows = list(client.query(plan["bq_etl_query"]).result())
        if not rows:
            return "ETL query returned no results. Graph is empty."

        nodes = {}
        final_relationships = []
        seen_relationships = set()

        for row in rows:
            row_nodes = {
                cfg["node_type"]: nodes.setdefault(
                    (str(row[cfg["id_column"]]), cfg["node_type"]),
                    Node(
                        id=str(row[cfg["id_column"]]),
                        type=cfg["node_type"],
                        properties={
                            "name": str(row[cfg["id_column"]]),
                            "description": f"A graph node representing a {cfg['node_type']} with the name {str(row[cfg['id_column']])}.",
                        },
                    ),
                )
                for cfg in plan["nodes"]
            }
            for rel in plan["relationships"]:
                source = row_nodes.get(rel["source"])
                target = row_nodes.get(rel["target"])
                if source and target:
                    rel_type = rel.get("type", "RELATED_TO")

                    # Now it's safe to access .id and create the key
                    relationship_key = (source.id, target.id, rel_type)

                    if relationship_key not in seen_relationships:
                        seen_relationships.add(relationship_key)
                        final_relationships.append(
                            Relationship(source=source, target=target, type=rel_type)
                        )

        graph_doc = GraphDocument(
            nodes=list(nodes.values()),
            relationships=final_relationships,
            source=Document(page_content="Dynamic Build"),
        )

        # ** NEW STEP: Explicitly generate and attach embeddings to each node **
        logging.info(f"Generating embeddings for {len(graph_doc.nodes)} nodes...")
        for node in graph_doc.nodes:
            node_content_for_embedding = node.properties.get("name", node.id)
            node.properties["embedding"] = embedding_service.embed_query(
                node_content_for_embedding
            )

        if cleanup_first:
            graph_store.cleanup()

        logging.info("Storing graph and embeddings in Spanner...")
        graph_store.add_graph_documents([graph_doc])

        return f"Success! Built graph with {len(nodes)} nodes and {len(final_relationships)} relationships."

    except Exception as e:
        return f"An unexpected error occurred during graph build: {e}"
    
# spanner tools

_qa_chain: Optional[SpannerGraphQAChain] = None

def get_spanner_graph_qa_chain(graph_store: SpannerGraphStore) -> SpannerGraphQAChain:
    """Initializes or returns the cached SpannerGraphQAChain."""
    global _qa_chain
    if _qa_chain:
        return _qa_chain

    # Initialize LLM
    llm = ChatVertexAI(
        model_name="gemini-2.5-flash",
        temperature=0,
        project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        location=os.environ.get("GOOGLE_CLOUD_LOCATION"),
    )

    # Initialize Chain
    _qa_chain = SpannerGraphQAChain.from_llm(
        llm,
        graph=graph_store,
        allow_dangerous_requests=True,
        verbose=True,
        return_intermediate_steps=True,
    )
    return _qa_chain


def get_spanner_schema_core(graph_store: SpannerGraphStore) -> str:
    """
    Retrieves the schema of the Spanner Graph, including node labels and properties.
    Use this to understand what data maps to which properties (e.g. is it 'Active' or 'active'?).
    """
    try:
        chain = get_spanner_graph_qa_chain(graph_store)
        if hasattr(chain.graph, "get_schema"):
            return chain.graph.get_schema
        # Fallback if get_schema property/method access differs
        return str(chain.graph.schema)
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"


def query_spanner_graph_core(question: str, graph_store: SpannerGraphStore) -> str:
    """
    Answers a question by querying the Spanner Graph.
    Returns the answer and the GQL query used.
    """
    try:
        chain = get_spanner_graph_qa_chain(graph_store)
        result = chain.invoke({"query": question})

        answer = result.get("result", "")
        intermediate_steps = result.get("intermediate_steps", [])

        gql_query = "N/A"
        formatted_result = {
            "answer": answer,
            "generated_gql": gql_query,
            "intermediate_steps": str(intermediate_steps),
        }

        for step in intermediate_steps:
            if isinstance(step, dict) and "query" in step:
                formatted_result["generated_gql"] = step["query"]
            elif isinstance(step, str) and "GRAPH" in step:
                formatted_result["generated_gql"] = step

        if not answer or answer.strip() == "[]":
            formatted_result["warning"] = (
                "The query returned no results. Consider checking the schema with `get_spanner_schema` or adjusting filters (e.g. case sensitivity)."
            )

        return json.dumps(formatted_result, indent=2)

    except Exception as e:
        return f"Error querying Spanner Graph: {str(e)}"

# agent definitions
def generate_build_plan_tool(
    user_request: str,
    schema_json: str,
    project_id: str,
    dataset_id: str,
    graph_name: str,
) -> Any:
    """
    Generates a detailed JSON build plan, including traversal tools with correct openCypher queries for Spanner Graph.
    """
    print("--- TOOL: Invoking Builder LLM to generate plan ---")
    # Use an f-string to dynamically insert the graph_name into the prompt examples
    builder_prompt = f"""
You are an expert graph data engineer for Spanner Graph. Your task is to generate a 'build plan' JSON object. This plan MUST include four keys:
1. `bq_etl_query`: A BigQuery SQL query to select columns for building the graph.
2. `nodes`: A list of objects defining each node with its `node_type` (label) and `id_column`.
3. `relationships`: A list of objects defining links. Each object MUST have three keys: 'source', 'target', and 'type'. The values for 'source' and 'target' MUST be the string values of the 'node_type' from the nodes list (e.g., "Server", "Employee"). They cannot be dictionaries. The 'type' MUST be an uppercase, snake_case string.
   **IMPORTANT**: If the DATABASE SCHEMA contains `foreign_keys`, you MUST automatically create relationships where the table with the foreign key is the 'source' and the `referenced_table` is the 'target'. You should assign a logical 'type' to these relationships (e.g. "HAS_ACCOUNT", "BELONGS_TO").
4. `traversal_tools`: A dictionary of complete, executable **openCypher** queries to traverse the graph relationships.

   --- CRITICAL SPANNER CYPHER RULES ---
   1.  Every query MUST begin with the 'GRAPH {graph_name}' directive followed by a space.
   2.  Query parameters MUST be prefixed with '@' (e.g., @app_id).
   3.  The relationship label in the MATCH clause is the full edge name constructed by joining the source type, relationship type, and target type with underscores.
   4.  Filter nodes using an explicit `WHERE` clause.
   5.  Self-Consistency Rule: When generating the `traversal_tools`, you MUST use the exact relationship `type` values you defined in the `relationships` section above to construct the edge labels.

   **Example of a correct query for a relationship defined as `source: "App", target: "Repo", type: "HAS_REPO"`:**
   The constructed edge label is `App_HAS_REPO_Repo`.
   The correct query for `get_repos_for_app` is:
   `GRAPH {graph_name} MATCH (a:App)-[:App_HAS_REPO_Repo]->(r:Repo) WHERE a.id = @app_id RETURN r.id AS id`

Your output MUST be ONLY the raw JSON object, without any markdown fences, comments, or other text.
"""
    # The context now explicitly includes the graph_name for the LLM
    context_string = f"CONTEXT:\nProject ID: {project_id}\nDataset ID: {dataset_id}\nGraph Name: {graph_name}\n\nDATABASE SCHEMA:\n{schema_json}"

    # Use the .invoke() method with a list of LangChain message objects
    response = ChatVertexAI(model="gemini-2.5-flash").invoke(
        [
            SystemMessage(content=f"{builder_prompt}\n\n{context_string}"),
            HumanMessage(content=user_request),
        ]
    )
    return response.content


def summarize_build_plan_tool(build_plan_json: str) -> Any:
    """
    Takes a raw JSON build plan and returns a human-readable summary.
    """
    print("--- TOOL: Invoking Summarizer LLM to generate summary ---")
    summarizer_prompt = (
        "You are a helpful project manager. Your task is to take a technical JSON build plan and describe it to a non-technical user. "
        "Do not show any code, SQL, or Cypher. Your output MUST have two sections:"
        "1. 'Graph Structure': Describe the entities (nodes) and the relationships between them in simple terms. Show the relationship flow (e.g., App -> Repo -> Table)."
        "2. 'Available Tools': List each tool from the 'traversal_tools' section. For each tool, provide a simple, one-sentence description of what it does (e.g., 'Given an App, this tool finds its code Repositories.')."
        "Your entire output must be in markdown."
    )
    response = ChatVertexAI(model="gemini-2.5-flash", temperature=0).invoke(
        f"{summarizer_prompt}\n\nJSON PLAN:\n{build_plan_json}"
    )
    return response.content

# utility tools


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

tools=[
    get_schema_wrapper,
    call_builder_tool_wrapper,
    summarize_build_plan_wrapper,
    initialize_graph_services_wrapper,
    execute_build_wrapper,
    execute_direct_traversal,
    answer_question_with_graph_rag,
    get_spanner_schema_wrapper,
    query_spanner_graph_wrapper,
]