# Developer Guide: Multi-Agent Quest Runtime

Welcome to the developer guide for the Multi-Agent Quest runtime. This document is designed to help developers understand how the system works under the hood and how to extend it with new agents and use cases.

---

## 1. System Architecture Overview

Multi-Agent Quest is a dynamic multi-agent system built on top of the **Google Agent Development Kit (ADK)**. Unlike static agent systems where agent collaborations are hardcoded, Multi-Agent Quest uses a **dynamic orchestration** pattern.

### Key Concepts:
*   **Root Agent**: The main entry point for user interaction. It acts as a dispatcher or router.
*   **Sub-Agents**: Specialized agents designed for specific domains (e.g., medical search, contract review, code migration).
*   **Session State**: A dynamic context associated with each user session. It determines which agents are active and what prompts are used.
*   **Tools**: In this system, **sub-agents are exposed as tools to the root agent**. This allows the root agent to delegate complex tasks to specialized sub-agents dynamically.

---

## 2. Dynamic Agent Loading (`ContextBasedToolset`)

The magic of Multi-Agent Quest lies in how it loads tools (sub-agents) based on the conversation context. This is handled by the `ContextBasedToolset` in `agent_bar_v2/tools/context_based_toolset.py`.

### How it works:
1.  When the root agent needs to interact with tools, it calls `get_tools()` on the `ContextBasedToolset`.
2.  The toolset reads the current **Session State** (via `ReadonlyContext`).
3.  **Predefined Workflows**: If `is_custom` is false, it reads `industry_id` and `use_case_id`. It then looks up the mapped agents in `agent_registry.py` using `get_predefined_use_case_sub_agents()`.
4.  **Custom Workflows**: If `is_custom` is true, it reads a list of agent IDs from `custom_agents` in the session state and loads them directly via `get_sub_agents()`.
5.  These agents are wrapped as `AgentTool` objects and returned to the root agent, making them available for the current turn.

> [!NOTE]
> This allows the system to support thousands of specialized agents without overloading the model's context window all at once. Only the agents relevant to the current use case are loaded.

---

## 3. Dynamic Prompting (`system_instructions_callback.py`)

Just as agents are loaded dynamically, the system prompt for the root agent is also constructed on the fly. This is managed by `set_system_instructions_callback` in `agent_bar_v2/callbacks/system_instructions_callback.py`.

### How it works:
*   **Predefined Use Cases**: It fetches a specific system prompt from `agent_registry.py` based on the `industry_id` and `use_case_id`.
*   **Custom Workflows**:
    *   Reads `custom_root_instructions` provided by the user.
    *   Appends mandatory instructions (e.g., "ALWAYS ask each sub-agent its role").
    *   Dynamically lists the available sub-agents and their descriptions so the root agent knows what they can do.
    *   Appends the `custom_workflow_map` to guide the sequence of agent interactions.

---

## 4. The Central Registry (`agent_registry.py`)

The `agent_bar_v2/subagents/agent_registry.py` file is the central nervous system for mapping the application's capabilities.

It contains two main maps:
1.  **`AGENT_REGISTRY_MAP`**: Maps a unique string ID (e.g., `"medical_search_agent"`) to the actual python instance of that agent.
2.  **`INDUSTRY_USE_CASE_AGENTS_MAP`**: Organizes use cases by industry and lists the `prompt` and the array of `agents` (by ID) that belong to that use case.

---

## 5. How to Add a New Agent

To add a new agent to the codebase, follow these steps:

### Step 1: Create the Agent Directory
Create a new directory under `agent_bar_v2/subagents/` corresponding to the industry (or `cross_industry`).
Example: `agent_bar_v2/subagents/retail/new_specialized_agent/`

### Step 2: Implement the Agent
At a minimum, you should create an `agent.py` file. Typical structure:
```python
from google.adk.agents import Agent
from google.adk.models import Gemini

AGENT_NAME = "new_specialized_agent"
AGENT_DESCRIPTION = "Detailed description of what this agent does."

root_agent = Agent(
    name=AGENT_NAME,
    model=Gemini(model="gemini-2.5-flash"),
    description=AGENT_DESCRIPTION,
    instruction="System instructions for this specific agent...",
    tools=[...], # Add any tools this agent needs
)
```

### Step 3: Register the Agent
Open `agent_bar_v2/subagents/agent_registry.py`:
1.  **Import** your agent at the top:
    ```python
    from ..subagents.retail.new_specialized_agent.agent import root_agent as new_specialized_agent
    ```
2.  **Add to `AGENT_REGISTRY_MAP`**:
    ```python
    AGENT_REGISTRY_MAP = {
        ...
        "new_specialized_agent": new_specialized_agent,
    }
    ```

---

## 6. How to Add a New Use Case

Once your agent is registered, you can add it to a new or existing use case.

### Step 1: Map the Use Case
In `agent_bar_v2/subagents/agent_registry.py`, locate `INDUSTRY_USE_CASE_AGENTS_MAP` and add your use case under the appropriate industry:

```python
INDUSTRY_USE_CASE_AGENTS_MAP = {
    "retail": {
        "new_cool_use_case": {
            "prompt": YOUR_NEW_PROMPT_STRING,
            "agents": ["new_specialized_agent", "customer_support"], # List the IDs from AGENT_REGISTRY_MAP
        },
    }
}
```

### Step 2: Define the Prompt
Ensure `YOUR_NEW_PROMPT_STRING` is defined (usually imported from a `prompts.py` file in your agent directory or `industry_prompts.py`). This prompt should instruct the root agent on how to use these specific sub-agents to solve the problem.

---

## 7. Agent Use Case Golden Template

For a fast-track way to create new use cases with a standard structure, refer to the [Agent Use Case Golden Template](agent_bar_v2/agent_use_case_golden_template/README.md).

This directory serves as a template or boilerplate for creating new Use Case Agents. It contains a "Golden Standard" structure that you can copy and modify:
*   `agent.py`: Main agent definition.
*   `prompts.py`: System instructions.
*   `tools.py`: Custom functions.
*   `config.py`: Configuration settings.

Developers are encouraged to use this template to maintain consistency across the repository. See the [README.md](agent_bar_v2/agent_use_case_golden_template/README.md) in that directory for step-by-step instructions on how to use it.

---

## 8. Evaluation Suite and Golden Datasets

To ensure that agents behave as expected, the repository includes an evaluation suite that uses **Golden Datasets**.

### Golden Datasets
Golden datasets are JSON files containing expected conversation flows, user prompts, and reference (golden) responses. They serve as the ground truth for evaluating agent performance.
*   **Location**: `test/eval/evalsets/`

### How it Works
The evaluation system uses the **AgentEvaluator** provided by the ADK. Pytest files in the `test/eval/` directory (e.g., `test_eval_cross_legal_guardian.py`) load these datasets and replay the conversation against the agent module.

### How to Run Evaluations
Developers can run these evaluations using `pytest`:
```bash
pytest test/eval/test_eval_cross_legal_guardian.py
```
You can also run all evaluations in the directory:
```bash
pytest test/eval/
```

---
## 9. Running Locally for Manual Testing

To test agents interactively and verify that changes do not break existing functionality, you can use the local development playground.

### Prerequisites
Ensure you have set up your environment variables by copying `.env.sample` to `.env` and filling in the required values.

### Starting the Playground
Run the following command from the project root to start the playground:

```bash
make playground
```

This will start a Streamlit app at `http://localhost:8501`. You can interact with the agents through this web interface.
Select the `agent_bar_v2` folder in the playground to interact with the agents developed in this runtime.

### Running Evaluations
To run automated evaluations using Golden Datasets, use `pytest` as described in Section 8. This is the best way to ensure no regressions were introduced.

## Summary for Demo staffers

When explaining this to users or developers, emphasize these points:
1.  **Dynamic Orchestration**: We don't build one giant agent. We build a squad of experts and load them only when needed.
2.  **Session Driven**: The UI sends state (industry/use case), and the backend instantly reconfigures itself.
3.  **Extensible**: Adding new capabilities is as simple as writing a Python file and registering it in the central map.


