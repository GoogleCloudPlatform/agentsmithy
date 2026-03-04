from google.adk.agents import Agent
from google.adk.tools.load_memory_tool import load_memory_tool
from .prompt import PROMPT
from .tools import create_bucket_tool, list_buckets_tool, get_bucket_details_tool, upload_file_gcs_tool, list_blobs_tool, get_file_contents_tool

# Create the GCS management agent
root_agent = Agent(
    name="GcsAgent",
    model="gemini-2.5-flash",
    description="Agent for managing and interacting with GCS buckets",
    instruction=PROMPT,
    tools=[
        create_bucket_tool,
        list_buckets_tool,
        get_bucket_details_tool,
        upload_file_gcs_tool,
        list_blobs_tool,
        get_file_contents_tool,
    ],
)