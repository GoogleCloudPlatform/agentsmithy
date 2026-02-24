from ..subagents.weather_agent.agent import root_agent as weather_agent
from ..subagents.cross_industry.contract_creation.agent import root_agent as contract_creation
from ..subagents.cross_industry.contract_review.agent import root_agent as contract_review
from ..subagents.cross_industry.proposal_writer.agent import root_agent as proposal_writer
from ..subagents.cross_industry.product_ad_generation.agent import (
    root_agent as product_ad_generation,
)
from ..subagents.hcls.patient_handover.agent import root_agent as patient_handover

from ..subagents.investment_strategy import root_agent as investment_strategy
from ..subagents.cyber_incident_response import root_agent as cyber_incident_response
from ..subagents.banking_modernization import root_agent as banking_modernization

from google.adk.tools.agent_tool import AgentTool


AGETN_REGISTRY_MAP = {
    "weather_agent": weather_agent,
    "contract_creation": contract_creation,
    "contract_review": contract_review,
    "proposal_writer": proposal_writer,
    "patient_handover": patient_handover,
    "investment_strategy": investment_strategy,
    "cyber_incident_response": cyber_incident_response,
    "banking_modernization": banking_modernization,
    "product_ad_generation": product_ad_generation,
}

INDUSTRY_USE_CASE_AGENTS_MAP = {
    "fis": {
        "insurance": ["contract_creation", "contract_review"],
        "investment_strategy": ["investment_strategy"],
        "modernization": ["banking_modernization"],
    },
    "hcls": {"clinical_handover": ["patient_handover"]},
    "cross": {
        "legal_guardian": ["contract_review"],
        "proposal_pitch_factory": ["proposal_writer", "product_ad_generation"],
    },
    "cyber": {"incident_response": ["cyber_incident_response"]},
}


def get_sub_agents(agents_id: [str]):
    """Return a list of agents from the registry"""
    agents = []
    if not agents_id:
        return agents
    for agent_id in agents_id:
        agent = AGETN_REGISTRY_MAP.get(agent_id)
        if agent is None:
            raise ValueError(f"Agent id '{agent_id}' not found in registry")
        agents.append(AgentTool(agent))
    return agents


def get_predefined_use_case_sub_agents(industry_id: str, use_case_id: str):
    """Return a list of agents for a predefined use case"""
    industry_use_cases = INDUSTRY_USE_CASE_AGENTS_MAP.get(industry_id)
    if industry_use_cases is None:
        raise ValueError(f"Industry id '{industry_id}' not found")

    agent_ids = industry_use_cases.get(use_case_id)
    if agent_ids is None:
        raise ValueError(f"Use case id '{use_case_id}' not found for industry '{industry_id}'")

    return get_sub_agents(agent_ids)
