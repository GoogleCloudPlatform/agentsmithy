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
# Insurance industry
curl -X POST http://localhost:8000/apps/agent_bar_v2/users/u_123/sessions/s_123 \
     -H "Content-Type: application/json" \
     -d '{ "user_id": "123", "industry_id": "insurance", "root_prompt_overwrite":"New instructions here" }'

# Weather industry
curl -X POST http://localhost:8000/apps/agent_bar_v2/users/u_321/sessions/s_321 \
     -H "Content-Type: application/json" \
     -d '{ "user_id": "321", "industry_id": "weather", "root_prompt_overwrite":"New instructions here" }'

# Delete the session
curl -X DELETE http://localhost:8000/apps/agent_bar_v2/users/u_123/sessions/s_123
curl -X DELETE http://localhost:8000/apps/agent_bar_v2/users/u_321/sessions/s_321
```

3. **Open the web interface:**
Notice that this url contains the user id and session id.
```
http://127.0.0.1:8000/dev-ui/?app=agent_bar_v2&session=s_123&userId=u_123
http://127.0.0.1:8000/dev-ui/?app=agent_bar_v2&session=s_321&userId=u_321
```

4. **Start Chatting:**
Return to the web interface, select the agent and the initialized session, and begin your interaction.

---

> **Note:** For more advanced configurations, refer to the [official ADK Runtime documentation](https://google.github.io/adk-docs/runtime/api-server/#test-locally).

