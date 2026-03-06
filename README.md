# Agent Bar v2 Agent Runtime

This repository contains the core runtime for **Agent Bar v2**, designed to facilitate the orchestration, execution, and management of multi-agent systems. It provides the underlying infrastructure for agent communication, state management, and tool integration.

## Setting up Locally

Configure your local environment by installing the **Agent Development Kit (ADK)**.

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the ADK
pip install google-adk
```

## Running the Agent

You can run the agent using the ADK CLI or the ADK Web Interface.

### Using the CLI

Run the agent directly from your terminal:

```bash
adk run agent_bar_v2
```

To replay a conversation or inject a specific agent state, use an `init.json` file:

```bash
# Rename the init.json.sample file to init.json, then run:
adk run --replay init.json agent_bar_v2
```

### Using the Web Interface

1. **Start the ADK web interface:**
```bash
adk web
```


2. **Initialize the session state:**
In a separate terminal, use `curl` to set the initial context for your session:
```bash
# Cross industry and legal guardian use case
curl -X POST http://localhost:8000/apps/agent_bar_v2/users/user/sessions/s_123 \
     -H "Content-Type: application/json" \
     -d '{ "user_id": "123", "industry_id": "cross", "use_case_id": "meeting_intelligence" }'

# Delete the session
curl -X DELETE http://localhost:8000/apps/agent_bar_v2/users/user/sessions/s_123
```

2.1. **Custom Agents workflows:**
```bash
curl -X POST http://localhost:8000/apps/agent_bar_v2/users/user/sessions/s_123 \
     -H "Content-Type: application/json" \
     -d '{  "user_id": "123", "industry_id": "cross", "use_case_id": "legal_guardian", "is_custom": true, "custom_agents": [ "contract_review" ], "custom_workflow_map": { "start": "contract_review", "contract_review": "end" }, "custom_root_instructions": "You are a highly skilled legal assistant specializing in contract analysis. Your goal is to identify potential risks, clarify complex terminology, and ensure compliance with standard regulatory frameworks. Please provide concise, actionable feedback for each document reviewed."}'
````


3. **Open the web interface:**
Notice that this url contains the user id and session id.
```
http://127.0.0.1:8000/dev-ui/?app=agent_bar_v2&session=s_123&userId=user
```

4. **Start Chatting:**
Return to the web interface, select the agent and the initialized session, and begin your interaction.

---

> **Note:** For more advanced configurations, refer to the [official ADK Runtime documentation](https://google.github.io/adk-docs/runtime/api-server/#test-locally).


## Generate configuration
locally
```
python -m agent_bar_v2.subagents.agent_registry --local-output
```
publish to GCS
```
python -m agent_bar_v2.subagents.agent_registry --gcs-bucket=ai-agent-bar-2026-stage-shared-config
```
