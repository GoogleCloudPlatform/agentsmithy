from google.adk.tools.base_toolset import BaseToolset
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_tool import BaseTool
from typing import List, Optional

from google.adk.tools.agent_tool import AgentTool

# from ..subagents.joke_agent import JokeAgent
# from ..subagents.finance_agent import FinanceAgent

from ..subagents.weather_agent.agent import root_agent as weather_agent
from ..subagents.contract_creation.agent import root_agent as contract_creation
from ..subagents.contract_review.agent import root_agent as contract_review
from ..subagents.content_archive_engine.agent import root_agent as content_archive_engine


INSURANCE_AGENTS = [AgentTool(contract_creation), AgentTool(contract_review)]
WEATHER_AGENTS = [AgentTool(weather_agent)]

INDUSTRY_AGENTS_MAP = {
    "insurance": INSURANCE_AGENTS,
    "weather": WEATHER_AGENTS,
    "content_archive_engine": content_archive_engine,
}


class ContextBasedToolset(BaseToolset):

    def __init__(self, prefix: str = "ctxts_"):
        self.tool_name_prefix = prefix

    async def get_tools(self, readonly_context: Optional[ReadonlyContext] = None) -> List[BaseTool]:
        print("SimpleMathToolset.get_tools() called. ")

        industry_id = readonly_context.state.get("industry_id")
        print(f"Getting agent for industry Id: {industry_id}")
        tools_to_return = INDUSTRY_AGENTS_MAP.get(industry_id, [])
        print(f"Providing tools (agents): {[t.name for t in tools_to_return]}")
        return tools_to_return

    async def close(self) -> None:
        # self.joke_agent.close()
        # self.finance_agent.close()
        pass
