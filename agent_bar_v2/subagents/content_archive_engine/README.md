
# Content Archive Engine

The Content Archive Engine is designed to monetize dormant video libraries by unlocking value from archives. It utilizes three specialized sub-agents:

1.  **Video Transcription Agent**: Generates transcripts and metadata.
2.  **Video Moments Agent**: Identifies viral clips and highlights.
3.  **Content Moderation Agent**: Ensures safety and compliance.

## Setup

1.  **Environment Variables**:
    Copy `.env.example` to `.env` and fill in your Google Cloud details:
    ```bash
    cp .env.example .env
    # Edit .env with your specific values
    ```

2.  **Install Dependencies**:
    ```bash
    make install
    ```

## Running the Agent

To start the agent's web interface:

```bash
make web
```

## Running Tests

To run the test suite:

```bash
make test
```
