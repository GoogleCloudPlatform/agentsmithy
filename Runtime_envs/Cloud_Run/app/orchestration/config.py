# ==============================================================================
# Copyright 2025 Google LLC. This software is provided as-is, without warranty
# or representation for any use or purpose. Your use of it is subject to your
# agreement with Google.
# ==============================================================================
"""Module that sets up environment variables from a sourced .env file."""
import os

import google

# Initialize Google Cloud and Vertex AI
credentials, project_id = google.auth.default()

SERP_API_KEY = os.getenv("SERPER_API_KEY", "unset")
PROJECT_ID = os.getenv("PROJECT_ID", project_id)
VERTEX_AI_LOCATION = os.getenv("REGION", "us-central1")
AGENT_BUILDER_LOCATION = os.getenv("AGENT_BUILDER_LOCATION", "us")
AGENT_INDUSTRY_TYPE = os.getenv("AGENT_INDUSTRY_TYPE", "unset")
AGENT_ORCHESTRATION_FRAMEWORK = os.getenv("AGENT_ORCHESTRATION_FRAMEWORK", "unset")
DATA_STORE_ID = os.getenv("DATA_STORE_ID", "unset")
