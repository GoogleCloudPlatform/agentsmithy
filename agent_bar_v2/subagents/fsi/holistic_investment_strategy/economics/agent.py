from pathlib import Path
from injector import Binder, Injector, SingletonScope
from google.adk.agents import BaseAgent, SequentialAgent
from .configuration import AgentConfig
from .data_lookup import DataProvider
from .sub_agents.query_generation_agent.agent import get_query_generation_agent
from .sub_agents.query_validation_agent.agent import get_query_validation_agent
from .sub_agents.query_runner_agent.agent import get_query_runner_agent
from .sub_agents.answer_generation_agent.agent import get_answer_generation_agent

# Configuration and Dependency Injection
CURRENT_DIR = Path(__file__).parent
CSV_PATH = CURRENT_DIR / "data" / "world_bank_data_2025.csv"

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
        name="NL2SQL_macroeconomic_agent",
        description="Analyzes global macroeconomic trends using a modular NL2SQL pipeline.",
        sub_agents=[
            query_gen,
            query_val,
            query_run,
            answer_gen,
        ],
    )
    return macro_agent

# For compatibility with legacy loading if needed
root_agent = create_root_agent()
