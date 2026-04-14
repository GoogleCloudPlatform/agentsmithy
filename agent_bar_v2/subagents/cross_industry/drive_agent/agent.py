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

import os
from google.adk.agents import Agent
from .prompt import PROMPT
from .tools import copy_and_replace_document_tool, save_document_tool, list_drive_documents_tool


drive_agent = Agent(
    name="DriveAgent",
    model=os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
    description="Drive Agent",
    instruction=PROMPT,
    tools=[
          copy_and_replace_document_tool,
          save_document_tool,
          list_drive_documents_tool,
    ],
)