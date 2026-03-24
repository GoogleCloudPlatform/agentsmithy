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

import os
from dotenv import load_dotenv

# Construct the path to the .env file in the root directory
# Uncomment this to load env vars for sharing file
# TODO improve this
# dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
# load_dotenv(dotenv_path)

from ..subagents.hcls.patient_handover.agent import root_agent as patient_handover
from ..subagents.hcls.medical_search_agent.agent import root_agent as medical_search_agent
from ..subagents.hcls.research_question_agent.agent import root_agent as research_question_writer
from ..subagents.hcls.hypothesis_agent.agent import root_agent as hypothesis_writer
from ..subagents.hcls.cardiology_consult.agent import root_agent as cardiology_consult
from ..subagents.hcls.provider_directory_search.agent import root_agent as provider_directory_search
from ..subagents.fsi.holistic_investment_strategy.economics.agent import root_agent as macro_agent
from ..subagents.fsi.holistic_investment_strategy.earnings.agent import root_agent as earnings_agent
from ..subagents.fsi.holistic_investment_strategy.finsights.agent import root_agent as finsights_agent
from ..subagents.fsi.banking_modernization_factory.discovery.agent import root_agent as discovery_agent
from ..subagents.fsi.banking_modernization_factory.migration.agent import root_agent as migration_agent
from ..subagents.fsi.cyber_incident_response.agent import root_agent as cyber_incident_response

from ..subagents.retail.global_campaign_manager.sub_agents.product_ad_generation.agent import (
    root_agent as retail_product_ad_generation,
)
from ..subagents.retail.global_campaign_manager.sub_agents.video_transcription.agent import (
    root_agent as video_transcription_agent,
)
from ..subagents.retail.customer_support_hub.sub_agents.conversational_shopping_assistant.agent import (
    root_agent as conversational_shopping_assistant,
)
from ..subagents.retail.customer_support_hub.sub_agents.customer_support.agent import root_agent as customer_support

from ..subagents.retail.intelligent_inventory_manager.sub_agents.catalog_enrichment.agent import (
    catalog_enrichment_agent,
)
from ..subagents.retail.intelligent_inventory_manager.sub_agents.nl2sql.agent import nl2sql_agent

from ..subagents.media.content_archive_engine.sub_agents.content_moderation.agent import (
    root_agent as content_moderation,
)

from ..subagents.media.content_archive_engine.sub_agents.video_analysis.agent import root_agent as video_analysis
from ..subagents.media.global_content_localizer.sub_agents.translation.agent import root_agent as translation_agent
from ..subagents.cross_industry.contract_creation.agent import root_agent as contract_creation
from ..subagents.cross_industry.legal_guardian.sub_agents.contract_review.agent import root_agent as contract_review

from ..subagents.cross_industry.cloud_finops_guru.agent import root_agent as finops_optimizer

from ..subagents.cross_industry.proposal_pitch_factory.sub_agents.proposal_writer.agent import (
    root_agent as proposal_writer,
)
from ..subagents.cross_industry.proposal_pitch_factory.sub_agents.product_ad_generation.agent import (
    root_agent as product_ad_generation,
)
from ..subagents.cross_industry.meeting_intelligence.sub_agents.transcription.agent import (
    root_agent as meeting_transcription,
)
from ..subagents.cross_industry.meeting_intelligence.sub_agents.video_analysis.agent import (
    root_agent as meeting_video_analysis,
)
from ..subagents.cross_industry.knowledge_graph_builder.agent import (
    root_agent as knowledge_graph_builder,
)

from ..subagents.cross_industry.storage_agent.agent import (
    root_agent as storage_access,
)

# Prompts

from .cross_industry.meeting_intelligence.prompts import SYSTEM_INSTRUCTION as CROSSIN_MEETING_INTELLIGENCE_PROMPT
from .cross_industry.legal_guardian.prompts import SYSTEM_INSTRUCTION as CROSSIN_LEGAL_GUARDIAN_PROMPT
from .cross_industry.proposal_pitch_factory.prompts import SYSTEM_INSTRUCTION as CROSSIN_PROPOSAL_PITCH_FACTORY_PROMPT
from .cross_industry.knowledge_graph_builder.prompts import SYSTEM_INSTRUCTION as CROSSIN_KNOWLEDGE_GRAPH_BUILDER_PROMPT
from .fsi.holistic_investment_strategy.prompts import SYSTEM_INSTRUCTION as HOLISTIC_INVESTMENT_STRATEGY_PROMPT
from .fsi.banking_modernization_factory.prompts import SYSTEM_INSTRUCTION as BANKING_MODERNIZATION_FACTORY_PROMPT
from .retail.global_campaign_manager.prompts import SYSTEM_INSTRUCTION as GLOBAL_CAMPAIGN_LAUNCHER_PROMPT
from .retail.customer_support_hub.prompts import SYSTEM_INSTRUCTION as CUSTOMER_SUPPORT_HUB_PROMPT
from .media.global_content_localizer.prompts import SYSTEM_INSTRUCTION as GLOBAL_CONTENT_LOCALIZER_PROMPT
from .retail.intelligent_inventory_manager.prompts import SYSTEM_INSTRUCTION as INTELLIGENT_INVENTORY_MANAGER_PROMPT

from .industry_prompts import (
    DEFAULT_PROMPT,
    HCLS_CLINICAL_HANDOVER_PROMPT,
    HCLS_RESEARCH_ACCELERATOR_PROMPT,
    MEDIA_CONTENT_ARCHIVE_ENGINE_PROMPT,
    HCLS_PROVIDER_SEARCH_AGENT_PROMPT,
    HCLS_CLINICAL_HANDOVER_PROMPT,
    HCLS_CARDIOLOGY_CONSULT_COPILOT_PROMPT,
    CYBER_INCIDENT_RESPONSE_PROMPT,
    CLOUD_FINOPS_GURU_PROMPT,
)

from google.adk.tools.agent_tool import AgentTool


AGENT_REGISTRY_MAP = {
    # from hcls
    "medical_search_agent": medical_search_agent,
    "research_question_writer": research_question_writer,
    "hypothesis_writer": hypothesis_writer,
    "provider_directory_search": provider_directory_search,
    "patient_handover": patient_handover,
    "cardiology_consult": cardiology_consult,
    # from fsi
    "macro_agent": macro_agent,
    "earnings_agent": earnings_agent,
    "finsights_agent": finsights_agent,
    "discovery_agent": discovery_agent,
    "migration_agent": migration_agent,
    # from retail
    "product_ad_agent": retail_product_ad_generation,
    "video_transcription_agent": video_transcription_agent,
    "customer_support": customer_support,
    "conversational_shopping_assistant": conversational_shopping_assistant,
    "catalog_enrichment_agent": catalog_enrichment_agent,
    "nl2sql_agent": nl2sql_agent,
    # from media
    "content_moderation": content_moderation,
    "transcription": meeting_transcription,
    "video_analysis": video_analysis,
    "translation_agent": translation_agent,
    # from cross industry
    "contract_creation": contract_creation,
    "contract_review": contract_review,
    "proposal_writer": proposal_writer,
    "product_ad_generation": product_ad_generation,
    "meeting_transcription": meeting_transcription,
    "meeting_video_analysis": meeting_video_analysis,
    "cyber_incident_response": cyber_incident_response,
    "knowledge_graph_builder": knowledge_graph_builder,
    "finops_optimizer": finops_optimizer,
    "storage_access": storage_access,
}

INDUSTRY_USE_CASE_AGENTS_MAP = {
    "hcls": {
        "research_accelerator": {
            "prompt": HCLS_RESEARCH_ACCELERATOR_PROMPT,
            "agents": ["medical_search_agent", "research_question_writer", "hypothesis_writer"],
        },
        "provider_search_agent": {
            "prompt": HCLS_PROVIDER_SEARCH_AGENT_PROMPT,
            "agents": ["provider_directory_search"],
        },
        "clinical_handover": {
            "prompt": HCLS_CLINICAL_HANDOVER_PROMPT,
            "agents": ["patient_handover", "storage_access"],
        },
        "cardiology_consult_copilot": {
            "prompt": HCLS_CARDIOLOGY_CONSULT_COPILOT_PROMPT,
            "agents": ["cardiology_consult"],
        },
    },
    "fsi": {
        "holistic_investment_strategy": {
            "prompt": HOLISTIC_INVESTMENT_STRATEGY_PROMPT,
            "agents": ["macro_agent", "earnings_agent", "finsights_agent"],
        },
        "banking_modernization_factory": {
            "prompt": BANKING_MODERNIZATION_FACTORY_PROMPT,
            "agents": ["discovery_agent", "migration_agent"],
        },
        # this agent is delegating the work to a sub agent
        "cyber_incident_response": {
            "prompt": CYBER_INCIDENT_RESPONSE_PROMPT,
            "agents": ["cyber_incident_response"],
        },
    },
    "retail": {
        "global_campaign_launcher": {
            "prompt": GLOBAL_CAMPAIGN_LAUNCHER_PROMPT,
            "agents": ["product_ad_agent", "video_transcription_agent"],
        },
        "customer_support_hub": {
            "prompt": CUSTOMER_SUPPORT_HUB_PROMPT,
            "agents": ["customer_support", "conversational_shopping_assistant"],
        },
        "intelligent_inventory_manager": {
            "prompt": INTELLIGENT_INVENTORY_MANAGER_PROMPT,
            "agents": ["catalog_enrichment_agent", "nl2sql_agent"],
        },
    },
    "media": {
        "content_archive_engine": {
            "prompt": MEDIA_CONTENT_ARCHIVE_ENGINE_PROMPT,
            "agents": ["content_moderation", "transcription", "video_analysis"],
        },
        "global_content_localizer": {
            "prompt": GLOBAL_CONTENT_LOCALIZER_PROMPT,
            "agents": ["translation_agent"],
        },
    },
    "cross": {
        "legal_guardian": {
            "prompt": CROSSIN_LEGAL_GUARDIAN_PROMPT,
            "agents": ["contract_review"],
        },
        "proposal_pitch_factory": {
            "prompt": CROSSIN_PROPOSAL_PITCH_FACTORY_PROMPT,
            "agents": ["proposal_writer", "product_ad_generation"],
        },
        "meeting_intelligence": {
            "prompt": CROSSIN_MEETING_INTELLIGENCE_PROMPT,
            "agents": ["meeting_transcription", "meeting_video_analysis"],
        },
        "knowledge_graph_builder": {
            "prompt": CROSSIN_KNOWLEDGE_GRAPH_BUILDER_PROMPT,
            "agents": ["knowledge_graph_builder"],
        },
        "cloud_finops_guru": {
            "prompt": CLOUD_FINOPS_GURU_PROMPT,
            "agents": ["finops_optimizer"],
        },
    },
}


def get_prompt_for_industry(industry_id: str, use_case_id: str) -> str:
    """Returns the prompt for the given industry ID, or the default prompt if not found."""
    try:
        return INDUSTRY_USE_CASE_AGENTS_MAP.get(industry_id).get(use_case_id).get("prompt")
    except Exception:
        return DEFAULT_PROMPT


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

    agent_ids = industry_use_cases.get(use_case_id).get("agents")
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
        "default_industry_use_cases": {
            industry_id: {
                use_case_id: use_case_config["agents"] for use_case_id, use_case_config in industry_config.items()
            }
            for industry_id, industry_config in INDUSTRY_USE_CASE_AGENTS_MAP.items()
        },
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
