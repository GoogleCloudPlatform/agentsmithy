from google.adk.agents import Agent
from google.adk.tools.load_memory_tool import load_memory_tool
from .prompt import PROMPT
from .tools import create_bucket_tool, list_buckets_tool, get_bucket_details_tool, upload_file_gcs_tool, list_blobs_tool, get_file_contents_tool

# Create the RAG management agent
gcs_agent = Agent(
    name="GcsAgent",
    model="gemini-2.5-flash",
    description="Agent for managing and interacting with GCS buckets",
    instruction=PROMPT,
    tools=[
        storage_tools.create_bucket_tool,
        storage_tools.list_buckets_tool,
        storage_tools.get_bucket_details_tool,
        storage_tools.upload_file_gcs_tool,
        storage_tools.list_blobs_tool,
        storage_tools.get_file_contents_tool,
    ],
)