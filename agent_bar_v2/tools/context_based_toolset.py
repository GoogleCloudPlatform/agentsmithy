import logging
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
from ..subagents.hcls.patient_handover.agent import root_agent as patient_handover_agent

INSURANCE_AGENTS = [AgentTool(contract_creation), AgentTool(contract_review)]
WEATHER_AGENTS = [AgentTool(weather_agent)]
HCLS_AGENTS = [AgentTool(patient_handover_agent)]
CROSSIN_LEGAL_GUARDIAN_AGENTS = [AgentTool(contract_review)]

INDUSTRY_USE_CASE_AGENTS_MAP = {
    "fis": {
        "insurance": INSURANCE_AGENTS,
    },
    "hcls": {"clinical_handover": HCLS_AGENTS},
    "cross": {"legal_guardian": CROSSIN_LEGAL_GUARDIAN_AGENTS},
}


class ContextBasedToolset(BaseToolset):

    def __init__(self, prefix: str = "ctxts_"):
        self.tool_name_prefix = prefix

    async def get_tools(self, readonly_context: Optional[ReadonlyContext] = None) -> List[BaseTool]:
        logging.info("SimpleMathToolset.get_tools() called. ")

        industry_id = readonly_context.state.get("industry_id")
        use_case_id = readonly_context.state.get("use_case_id")
        logging.info(f"Getting agent for industry Id: {industry_id} and use case Id: {use_case_id}")
        try:
            tools_to_return = INDUSTRY_USE_CASE_AGENTS_MAP.get(industry_id).get(use_case_id)
        except Exception:
            logging.warning("No agents found for this industry and use case.")
            tools_to_return = []

        logging.info(f"Providing tools (agents): {[t.name for t in tools_to_return]}")
        return tools_to_return

    async def close(self) -> None:
        pass
