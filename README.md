# Agent Bar v2


## Introduction

**Agent Bar v2** is a robust multi-agent runtime designed to facilitate the orchestration, execution, and management of complex multi-agent systems. It provides the underlying infrastructure for agent communication, dynamic state management, tool integration, and industry-specific use cases.

[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.svg)](https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/srastatter/agent-bar-v2-agent-runtime.git&cloudshell_tutorial=setup.md)

> **Note:** You can quickly set up the environment by clicking the **Open in Cloud Shell** button above, which will launch an interactive tutorial. For a detailed step-by-step guide on infrastructure provisioning and deployment, please refer to [**setup.md**](setup.md).

### Folder Structure

The repository is organized as follows:
- `agent_bar_v2/`: The core runtime application.
  - `subagents/`: Contains specialized sub-agents categorized by industry (e.g., `cross_industry`, `fsi`, `hcls`, `media`, `retail`).
    - `agent_registry.py`: The central registry mapping available agents and industry-specific prompts based on session state configuration.
  - `callbacks/`: Event handlers for agent interactions (e.g., System Instructions callback).
- `tools/`: Reusable toolsets and context-based utilities for agents.
- `test/`: Evaluation scripts and session data for testing the various agents and prompts.
- `assets/`: UI assets, including custom CSS for the web interface.

## Setup

For comprehensive setup, infrastructure provisioning (Terraform), and deployment instructions, please follow the [**Setup Guide (setup.md)**](setup.md).

### Quick Start (Local Development)

If you just want to run the agent locally for development:

1. **Prerequisites:**
   - Python 3.10+
   - `pip` or `uv` for dependency management.

2. **Installation:**
   ```bash
   # Create and activate a virtual environment
   python3 -m venv .venv
   source .venv/bin/activate

   # Install the ADK and dependencies
   pip install google-adk
   pip install -e .
   ```

## Testing with the ADK Web UI

The ADK Web UI provides an interactive interface for chatting with the agents. Agent Bar v2 dynamically loads specific sub-agents and prompts based on the session's **industry** and **use case** configuration.

1. **Start the ADK web interface:**
```bash
adk web
```

2. **Initialize the session state:**
Agent Bar v2 relies on the session state to determine which agents to activate. This mapping is defined in `agent_bar_v2/subagents/agent_registry.py`. By changing the `industry_id` and `use_case_id` in the state initialization, you dynamically swap the agents handling the conversation.

In a separate terminal, use `curl` to set the initial context for your session (e.g., cross-industry meeting intelligence):
```bash
curl -X POST http://localhost:8000/apps/agent_bar_v2/users/user/sessions/s_123 \
     -H "Content-Type: application/json" \
     -d '{ "user_id": "123", "industry_id": "cross", "use_case_id": "meeting_intelligence" }'
```

*To explore different use cases, refer to the `INDUSTRY_USE_CASE_AGENTS_MAP` dictionary in `agent_registry.py` for valid `industry_id` and `use_case_id` combinations.*

2.1. **Custom Agents Workflow:**
You can also override the default registry and define custom workflows directly in the state:
```bash
curl -X POST http://localhost:8000/apps/agent_bar_v2/users/user/sessions/s_123 \
     -H "Content-Type: application/json" \
     -d '{  "user_id": "123", "industry_id": "cross", "use_case_id": "legal_guardian", "is_custom": true, "custom_agents": [ "contract_review" ], "custom_workflow_map": { "start": "contract_review", "contract_review": "end" }, "custom_root_instructions": "You are a highly skilled legal assistant..."}'
```

3. **Open the web interface:**
Navigate to the URL containing your specific user ID and session ID:
```text
http://127.0.0.1:8000/dev-ui/?app=agent_bar_v2&session=s_123&userId=user
```

4. **Start Chatting:**
Select the agent and the initialized session in the web UI, and begin your interaction.

## Generating the Configuration

The agent registry configuration can be exported locally or published directly to a Google Cloud Storage (GCS) bucket.

**Generate Locally:**
```bash
python -m agent_bar_v2.subagents.agent_registry --local-output
```

**Publish to GCS:**
```bash
python -m agent_bar_v2.subagents.agent_registry --gcs-bucket=ai-agent-bar-2026-stage-shared-config
```
