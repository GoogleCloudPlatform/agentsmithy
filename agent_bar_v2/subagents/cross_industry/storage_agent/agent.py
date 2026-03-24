import os
from google.adk.agents import Agent
from google.adk.tools.load_memory_tool import load_memory_tool
from .prompt import SYSTEM_INSTRUCTIONS
from .tools import create_bucket_tool, list_buckets_tool, get_bucket_details_tool, upload_file_gcs_tool, list_blobs_tool, get_file_contents_tool

# Create the GCS management agent
root_agent = Agent(
    name="GcsAgent",
    model=os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview"),
    description="Agent for managing and interacting with GCS buckets",
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[
        create_bucket_tool,
        list_buckets_tool,
        get_bucket_details_tool,
        upload_file_gcs_tool,
        list_blobs_tool,
        get_file_contents_tool,
    ],
)