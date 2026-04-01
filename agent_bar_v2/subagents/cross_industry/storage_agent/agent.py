# Copyright 2026 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import Agent
from google.adk.tools.load_memory_tool import load_memory_tool
from .prompt import SYSTEM_INSTRUCTION
from .tools import create_bucket_tool, list_buckets_tool, get_bucket_details_tool, upload_file_gcs_tool, list_blobs_tool, get_file_contents_tool

# Create the GCS management agent
root_agent = Agent(
    name="storage_access",
    model=os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
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