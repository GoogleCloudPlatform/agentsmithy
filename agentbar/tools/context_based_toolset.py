from google.adk.tools.base_toolset import BaseToolset
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_tool import BaseTool
from typing import List, Optional

from google.adk.tools.agent_tool import AgentTool

from ..subagents.joke_agent import JokeAgent
from ..subagents.finance_agent import FinanceAgent


class ContextBasedToolset(BaseToolset):

    def __init__(self, prefix: str = "ctxts_"):
        self.tool_name_prefix = prefix

        self.joke_agent = JokeAgent()
        self.finance_agent = FinanceAgent()

    async def get_tools(self, readonly_context: Optional[ReadonlyContext] = None) -> List[BaseTool]:
        print("SimpleMathToolset.get_tools() called. ")

        tools_to_return = [AgentTool(self.joke_agent)]
        if readonly_context.state.get("industry_id") == "finance":
            tools_to_return.append(AgentTool(self.finance_agent))

        print(f"Providing tools: {[t.name for t in tools_to_return]}")
        return tools_to_return

    async def close(self) -> None:
        # self.joke_agent.close()
        # self.finance_agent.close()
        pass
