import os
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

import os
from pathlib import Path
from injector import Binder, Injector, SingletonScope
from google.adk.agents import BaseAgent, SequentialAgent
from .configuration import AgentConfig
from .data_lookup import DataProvider
from .sub_agents.query_generation_agent.agent import get_query_generation_agent
from .sub_agents.query_validation_agent.agent import get_query_validation_agent
from .sub_agents.query_runner_agent.agent import get_query_runner_agent
from .sub_agents.answer_generation_agent.agent import get_answer_generation_agent
from .config import MACROECONOMICS_BUCKET_NAME

# Configuration and Dependency Injection
CURRENT_DIR = Path(__file__).parent
CSV_PATH = f"gs://{MACROECONOMICS_BUCKET_NAME}/fsi/economics/data/world_bank_data_2025.csv"

def configure_macro_agent(binder: Binder) -> None:
    binder.bind(AgentConfig, to=AgentConfig(), scope=SingletonScope)
    binder.bind(DataProvider, to=DataProvider(csv_data=CSV_PATH), scope=SingletonScope)

def create_root_agent() -> BaseAgent:
    """Creates the root sequential agent with all its sub-agents."""
    injector = Injector(configure_macro_agent)
    
    query_gen = get_query_generation_agent(injector)
    query_val = get_query_validation_agent(injector)
    query_run = get_query_runner_agent(injector)
    answer_gen = get_answer_generation_agent(injector)

    macro_agent = SequentialAgent(
        name=AGENT_NAME,
        description=AGENT_DESCRIPTION,
        sub_agents=[
            query_gen,
            query_val,
            query_run,
            answer_gen,
        ],
    )
    return macro_agent

AGENT_NAME = "macro_agent"
AGENT_DESCRIPTION = "Analyzes global economic trends, central bank policies, and market indicators to provide macroeconomic insights."


# Model configuration
GEMINI_MODEL_CONFIG = Gemini(
    model=os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash"),
    generation_config=types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        max_output_tokens=65536,
    ),
    retry_options=types.HttpRetryOptions(attempts=3),
)

root_agent = Agent(
    name=AGENT_NAME,
    model=GEMINI_MODEL_CONFIG,
    description=AGENT_DESCRIPTION,
    instruction=prompts.SYSTEM_INSTRUCTION,
    tools=tools.tools,
)
