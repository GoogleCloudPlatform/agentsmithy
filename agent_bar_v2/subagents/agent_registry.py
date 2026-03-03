
import os
from dotenv import load_dotenv

# Construct the path to the .env file in the parent directory (agent_bar_v2)
dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path)

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


AGENT_REGISTRY_MAP = {
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
    "fsi": {
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
        agent = AGENT_REGISTRY_MAP.get(agent_id)
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


def main():


    import argparse
    import json
    from google.cloud import storage

    parser = argparse.ArgumentParser(description="CLI for Agent Registry")
    parser.add_argument("--local-output", action="store_true", help="If present, the file will be stored locally")
    parser.add_argument("--gcs-bucket", type=str, help="GCS bucket name to upload the JSON output")
    parser.add_argument(
        "--output-filename",
        type=str,
        default="agent_bar_v2_config.json",
        help="Name of the file to create in GCS",
    )
    args = parser.parse_args()

    # Prepare the data to be exported
    registry_data = {
        "available_agents": [
            {
                "id": agent_id,
                "name": agent.name,
                "description": agent.description,
            }
            for agent_id, agent in AGENT_REGISTRY_MAP.items()
        ],
        "default_industry_use_cases": INDUSTRY_USE_CASE_AGENTS_MAP,
    }

    # Initialize GCS client and upload the data
    if args.local_output:
        try:
            with open(args.output_filename, "w") as f:
                f.write(json.dumps(registry_data, indent=4))
                print(f"Successfully saved registry configuration locally to {args.output_filename}")
        except Exception as e:
            print(f"Failed to save locally: {e}")
    else:
        if not args.gcs_bucket:
            parser.error("--gcs-bucket is required when --local-output is not set")
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(args.gcs_bucket)
            blob = bucket.blob(args.output_filename)

            blob.upload_from_string(data=json.dumps(registry_data, indent=4), content_type="application/json")
            print(f"Successfully uploaded registry configuration to gs://{args.gcs_bucket}/{args.output_filename}")
        except Exception as e:
            print(f"Failed to upload to GCS: {e}")


if __name__ == "__main__":
    main()
