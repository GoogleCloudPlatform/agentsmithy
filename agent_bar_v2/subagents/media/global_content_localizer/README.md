# Global Content Localizer Agent

This agent expands streaming reach by accurately localizing content for new regions. It can generate subtitles and translate content (text and images) using a specialized translation sub-agent.

## Prerequisites

- Python 3.10+
- `uv` (optional, but recommended for dependency management)

## Setup

1.  **Clone the repository** (if you haven't already).
2.  **Navigate to the agent directory**:
    ```bash
    cd global_content_localizer
    ```
3.  **Install dependencies**:
    ```bash
    make install
    ```
    This command uses `uv` to create a virtual environment and install all required packages defined in `pyproject.toml`.

## Environment Configuration

Ensure you have a `.env` file in the `global_content_localizer` directory with the following variables:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GCS_BUCKET=your-gcs-bucket-name
```

## Running the Agent

To start the agent's web interface:

```bash
make web
```

**Note**: This command runs the agent from the parent directory context (`..`) to ensure correct agent discovery. You will see all agents in the parent directory, but `global_content_localizer` will be available in the list.

## Testing the Agent

1.  **Open the Web UI**: Go to the URL provided by the `make web` command (e.g., `http://127.0.0.1:8000`).
2.  **Select the Agent**: Choose `global_content_localizer` from the list of available agents.
3.  **Interact with the Agent**:
    -   **Type a request**: e.g., "Translate 'Hello world' to Spanish."
    -   **Upload separate files**: You can upload text files or images containing text.
    -   **Ask for "dubbing"**: The agent will explain its capability (providing translated text for voice-over).
4.  **Verify Output**: Check if the agent correctly identifies the language and provides the translation.

### Example Scenarios

-   **Scenario 1: Simple Translation**
    -   User: "Translate this to French: 'The quick brown fox jumps over the lazy dog.'"
    -   Agent: Should use the translation tool and return the French text.

-   **Scenario 2: Image Translation**
    -   User: Uploads an image with text. "What does this sign say in English?"
    -   Agent: Should use `pic_to_text` (via sub-agent) and then translate it.

-   **Scenario 3: Localization Request**
    -   User: "I have a new episode of 'Mystery Island'. I need subtitles for Brazil and Japan."
    -   Agent: Should acknowledge the request and ask for the content (transcript or video file) to begin the process for Portuguese (Brazil) and Japanese.
