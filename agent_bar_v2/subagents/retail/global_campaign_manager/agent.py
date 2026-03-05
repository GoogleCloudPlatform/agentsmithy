# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
import google.auth
import google.cloud.storage as storage

from .sub_agents.product_ad_generation.agent import product_ad_agent
from .sub_agents.video_transcription.agent import video_transcription_agent
from .prompts import GLOBAL_CAMPAIGN_MANAGER_INSTRUCTIONS

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


root_agent = Agent(
        name="global_campaign_manager",
        model="gemini-2.5-flash",
        description=(
            "You are a Global Campaign Manager Agent, a helpful AI agent and "
            "creative partner that generates multi-scene video advertisements. "
        ),
        instruction=GLOBAL_CAMPAIGN_MANAGER_INSTRUCTIONS,
        sub_agents=[product_ad_agent, video_transcription_agent],
    )
