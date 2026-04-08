# Evaluate

This directory contains the evaluation and test suite for the Multi-Agent Quest.

## Local Environment Setup

Follow these steps to prepare your local environment for testing and evaluation:

### 1. Prerequisites
*   Ensure you have the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed.
*   Install [uv](https://docs.astral.sh/uv/getting-started/installation/) for Python package management.

### 2. Authentication
Authenticate your local environment with Google Cloud to allow the agents to access Google Cloud services:
```bash
gcloud auth application-default login
```

### 3. Dependency Installation
Sync the project dependencies and create a virtual environment:
```bash
uv sync
```

### 4. Configuration
Create a `.env` file in `agent_bar_v2/` (you can use `.env.sample` as a template) and populate it with the required values (Project ID, Location, etc.).

## Running Evaluations

To run the full test suite using your environment variables:

```bash
uv run pytest test/ --envfile agent_bar_v2/.env
```

## Directory Structure

The `test/` directory is organized as follows:

*   `eval/`: Contains Python test files that use the `AgentEvaluator` to run evaluations.
    *   `evalsets/`: Contains the JSON evaluation datasets (golden responses and conversation flows).
        *   `sessions/`: Utilities and raw session data.
            *   `convert_sessions.py`: A utility script to transform exported ADK sessions into the standard `evalset` JSON format.

## Adding New Evaluations

### 1. Create an Evaluation Dataset (evalset)
Evaluation datasets are JSON files stored in `test/eval/evalsets/`. They define the conversation flow and expected agent behavior.

**Tip:** If you have an exported session from an ADK-based application, you can place the session JSON in `test/eval/evalsets/sessions/` and run the `convert_sessions.py` utility to automatically generate the `evalset` format.

### 2. Create a Python Test File
In `test/eval/`, create a new Python file (e.g., `test_eval_new_feature.py`)

Pytest is configured to detect these `eval()` functions automatically.

### Generating Reports
If you have `pytest-html` installed, you can generate an HTML report:
```bash
uv run pytest test/ --envfile agent_bar_v2/.env --html=report.html
```

## References

For more detailed information on ADK evaluation, including advanced configuration and evaluation metrics, please refer to the official [ADK Evaluation Documentation](https://google.github.io/adk-docs/evaluate/).