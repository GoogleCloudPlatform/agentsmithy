# Copyright 2026 Google LLC
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

"""Tools for the Use Case Agent."""

import os
from google.adk.tools import AgentTool, load_artifacts

# Import sub-agents
from .sub_agents import (
    transcription_agent,
    video_analysis_agent,
    content_moderation_agent,
)

# Wrap sub-agents in AgentTool
transcription_tool = AgentTool(transcription_agent)
video_analysis_tool = AgentTool(video_analysis_agent)
content_moderation_tool = AgentTool(content_moderation_agent)