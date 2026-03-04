# Customer Support Hub

This agent pack serves as a central hub for customer support and product search inquiries. It orchestrates two sub-agents:

1.  **Customer Support**: Handles returns, refunds, and product condition inquiries.
2.  **Conversational Shopping Assistant**: Assists with product search and catalog exploration.

## Architecture

The hub agent uses `google.adk.agents.LlmAgent` to route user queries to the appropriate sub-agent based on the conversation context.

## Sub-Agents

-   `src/agents/customer_support_hub/sub_agents/customer_support`: Based on the `customer_support` starter pack.
-   `src/agents/customer_support_hub/sub_agents/conversational_shopping_assistant`: Based on the `vais-product-search` starter pack (renamed).

## Setup

1.  Install dependencies:
    ```bash
    pip install .
    ```
2.  Set environment variables:
    -   `GOOGLE_CLOUD_PROJECT`: Your GCP project ID.
    -   `DATASTORE_ID`: Vertex AI Search Datastore ID (required for Shopping Assistant).
    -   `LLM_MODEL`: Gemini model to use (default: `gemini-2.5-flash`).

## Usage

Run the agent:
```bash
python main.py
```
