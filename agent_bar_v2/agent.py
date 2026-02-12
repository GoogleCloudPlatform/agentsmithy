from google.adk.agents.llm_agent import Agent

from .callbacks.system_instructions_callback import (
    set_system_instructions_callback,
)

from .tools.context_based_toolset import ContextBasedToolset
from .subagents.weather_agent.agent import root_agent as weather_agent
from .subagents.contract_creation.agent import root_agent as contract_creation
from .subagents.contract_review.agent import root_agent as contract_review

context_based_toolset = ContextBasedToolset()

root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="A helpful assistant for user questions.",
    instruction="You are a very helpful assistant",
    before_model_callback=set_system_instructions_callback,
    tools=[context_based_toolset],
    sub_agents=[weather_agent, contract_creation, contract_review],
)
