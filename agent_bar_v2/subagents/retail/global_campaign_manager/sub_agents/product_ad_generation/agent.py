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

import os
import google.auth
from google.adk.agents import Agent
from google.adk.models import Gemini

from .config import BUCKET_NAME, LOCATION, PROJECT_ID
from . import prompts
from . import tools
from .callbacks import inline_data_processing


_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# if not PROJECT_ID or not LOCATION or not BUCKET_NAME:
#     raise EnvironmentError(
#         "Missing required environment variables (GOOGLE_CLOUD_PROJECT, "
#         "GOOGLE_CLOUD_LOCATION, GCS_BUCKET) in your .env file."
#     )

print(f"Loaded config: Project={PROJECT_ID}, Location={LOCATION}, Bucket={BUCKET_NAME}")


AGENT_NAME = "product_ad_agent"
AGENT_DESCRIPTION = "You are a Product Ad Generation Agent, a helpful AI agent and creative partner that generates multi-scene video advertisements. Your process is interactive and split into precise steps."

# Model configuration
GEMINI_MODEL_CONFIG = Gemini(
    model="gemini-2.5-flash",
)

root_agent = Agent(
    name=AGENT_NAME,
    model=GEMINI_MODEL_CONFIG,
    description=AGENT_DESCRIPTION,
    instruction=prompts.SYSTEM_INSTRUCTION,
    tools=tools.tools,
    before_agent_callback=inline_data_processing,
)