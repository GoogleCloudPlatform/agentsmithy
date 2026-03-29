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

"""Entrypoint for the patient handover agent."""

import os
from datetime import datetime

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from . import prompts
from . import tools

DEFAULT_MODEL = "gemini-2.5-flash"


AGENT_NAME = "patient_handover"
AGENT_DESCRIPTION = "Provides shift handover and endorsement reports for medical patients."

# Model configuration
GEMINI_MODEL_CONFIG = Gemini(
    model="gemini-2.5-flash",
)


def initialize_state(callback_context: CallbackContext) -> None:
    start_time = datetime.strptime("2024-06-07 07:30:00", "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime("2024-06-07 19:30:00", "%Y-%m-%d %H:%M:%S")

    callback_context.state["shifts"] = [
        {"start_time": start_time.isoformat(), "end_time": end_time.isoformat()}
    ]
    # callback_context.state["patients"] = ["MHID123456789"]

    callback_context.state["section_model"] = os.environ.get(
        "SECTION_MODEL_NAME", DEFAULT_MODEL
    )
    callback_context.state["summary_model"] = os.environ.get(
        "SUMMARY_MODEL_NAME", DEFAULT_MODEL
    )


root_agent = Agent(
    name=AGENT_NAME,
    model=GEMINI_MODEL_CONFIG,
    description=AGENT_DESCRIPTION,
    instruction=prompts.SYSTEM_INSTRUCTION,
    before_agent_callback=initialize_state,
    tools=[
        tools.list_available_shifts,
        tools.list_patients,
        tools.generate_shift_endorsement,
    ],
)
