# Agent Use Case Golden Template

This directory serves as the **Golden Standard** for creating new Use Case Agents in the `agent-bar-v2-agent-runtime` repository.

## Directory Structure

```
agent_bar_v2/
└── [new_use_case_name]/
    ├── __init__.py           # Exposes the root_agent of this use case
    ├── agent.py              # Main agent definition and configuration
    ├── prompts.py            # System instructions and prompt templates
    ├── tools.py              # Tool functions (typed and documented)
    ├── config.py             # Environment variables and configuration settings
    └── sub_agents/           # Folder for specialized sub-agents
        ├── __init__.py
        └── [sub_agent_name]/
            ├── __init__.py
            └── agent.py      # Sub-agent definition
```

## Creating a New Use Case Agent

1.  **Copy this folder** and rename it to your use case (e.g., `technical_support`).
2.  **Update `prompts.py`**: define `SYSTEM_INSTRUCTION` with the persona and goals.
3.  **Update `config.py`**: ensure environment variables (like `GCS_BUCKET`) are correctly mapped.
4.  **Update `tools.py`**: define any custom Python functions needed. Ensure type hints and docstrings are present.
4.  **Update `agent.py`**:
    - Set `AGENT_NAME` and `AGENT_DESCRIPTION`.
    - Configure the `Gemini` model parameters (temperature, etc.).
    - Pass tools and sub-agents to the `Agent` constructor.
5.  **Add Sub-Agents**: 
    - Create new folders under `sub_agents/` following the same `agent.py` pattern.
    - Import them into the main `agent.py`.

## Key Standards to Follow

-   **Imports**: Use `from google.adk.agents import Agent` and `from google.adk.models import Gemini`.
-   **Documentation**: All tools must have docstrings explaining arguments and return values.
-   **Type Hints**: Use standard Python type hints for all tool arguments.
-   **Naming**: Use `snake_case` for directory names and file names.

## Registering Your Agent

Once created, you must register your agent in the global `ContextBasedToolset`:

1.  Open `agent_bar_v2/tools/context_based_toolset.py`.
2.  Import your agent: `from ..subagents.[your_folder] import root_agent as [your_agent_alias]`.
3.  Add it to the `INDUSTRY_USE_CASE_AGENTS_MAP`.
