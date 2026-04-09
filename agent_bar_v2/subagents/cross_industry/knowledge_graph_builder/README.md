# Knowledge Graph Builder Agent

An agent that specializes in reading BigQuery data and proposing data models to build knowledge graphs. It guides the user through discovering data, defining relationships, and generating a build plan.

## Project Structure

```
knowledge_graph_builder/
├── README.md          # This file
├── __init__.py        # Exports root_agent
├── agent.py           # ADK Agent definition
├── config.py          # Configuration settings (Project ID, Dataset ID, etc.)
├── prompts.py         # System instructions and operational workflow
└── tools.py           # Tools for BigQuery exploration and build plan generation
```

## Operational Workflow

The agent is designed to guide the user through the following steps:

1.  **Show Available Data**: List the datasets that are available for exploration.
2.  **Discovery**: Inspect the schema of a chosen dataset to identify tables and columns.
3.  **Present & Wait**: Present the discovered entities and automatically suggest relationships based on foreign keys. The agent will then wait for user confirmation or additional relationship definitions.
4.  **Planning**: Generate a detailed JSON build plan for creating the knowledge graph.
5.  **Summarization**: Provide a human-readable summary of the generated build plan.

## Configuration

The agent relies on the following environment variables (configured in `config.py`):

*   `GOOGLE_CLOUD_PROJECT`: The Google Cloud project ID.
*   `GOOGLE_CLOUD_LOCATION`: The Google Cloud location (e.g., us-central1).
*   `GCP_DATASET_ID`: The BigQuery dataset ID to explore (defaults to "retail").
*   `GRAPH_NAME`: The name of the graph to be built.

## Tools

The agent has access to the following tools:

| Tool | Description |
|---|---|
| `get_bq_datasets` | Returns a list of approved BigQuery datasets for exploration. |
| `get_schema_wrapper` | Inspects a BigQuery dataset and returns table schemas, including primary and foreign keys. |
| `call_builder_tool_wrapper` | Generates a JSON build plan based on the user's request and the dataset schema. |
| `summarize_build_plan_wrapper` | Generates a human-readable summary of the stored build plan. |
