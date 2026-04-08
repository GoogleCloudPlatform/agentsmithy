# Agent Bar v2


## Introduction

**Agent Bar v2** is a robust multi-agent runtime designed to facilitate the orchestration, execution, and management of complex multi-agent systems. It provides the underlying infrastructure for agent communication, dynamic state management, tool integration, and industry-specific use cases.

[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.svg)](https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/srastatter/agent-bar-v2-agent-runtime.git&cloudshell_tutorial=setup.md)

> **Note:** You can quickly set up the environment by clicking the **Open in Cloud Shell** button above, which will launch an interactive tutorial. For a detailed step-by-step guide on infrastructure provisioning and deployment, please refer to [**setup.md**](setup.md).

### Folder Structure

The repository is organized as follows:
- `agent_bar_v2/`: The core runtime application.
  - `subagents/`: Contains specialized sub-agents categorized by industry (e.g., `cross_industry`, `fsi`, `hcls`, `media`, `retail`).
    - `agent_registry.py`: The central registry mapping available agents and industry-specific prompts based on session state configuration.
  - `callbacks/`: Event handlers for agent interactions (e.g., System Instructions callback).
- `tools/`: Reusable toolsets and context-based utilities for agents.
- `test/`: Evaluation scripts and session data for testing the various agents and prompts.
- `assets/`: UI assets, including custom CSS for the web interface.



## Use Cases by Industry

This section outlines the predefined use cases available in Agent Bar v2, organized by industry. These use cases are mapped in `agent_bar_v2/subagents/agent_registry.py`.

### 🏥 Health and Life Sciences (HCLS)

| Use Case | Problem Statement | Agents Used | Description |
| :--- | :--- | :--- | :--- |
| **Cut Research Time From Weeks to Minutes** | Slow drug development cycles due to manual synthesis of vast research literature and difficulties generating compliant datasets for model testing. | 1. [Medical search agent](agent_bar_v2/subagents/hcls/medical_search_agent/agent.py)<br>2. [Research question agent](agent_bar_v2/subagents/hcls/research_question_agent/agent.py)<br>3. [Hypothesis agent](agent_bar_v2/subagents/hcls/hypothesis_agent/agent.py) | The mission with this agent journey is to accelerate drug trials by synthesizing PubMed research and generating privacy-safe patient datasets. |
| **Match Patients with Right Medical Specialists Fast** | Difficulty for patients and coordinators in quickly identifying the right specialists within complex provider directories, delaying access to care. | 1. [Provider Directory Search](agent_bar_v2/subagents/hcls/provider_directory_search/agent.py) | The mission with this agent journey is to improve patient access by finding specialists through an automated directory search. |
| **Reduce Dangerous Medical Errors During Transitions** | A high risk of medical errors during patient shift changes due to incomplete or inconsistent transfer of critical clinical information. | 1. [Nurse Handover Agent](agent_bar_v2/subagents/hcls/patient_handover/agent.py) | The mission with this agent journey is to manage safe shift changes by summarizing critical patient vitals and risks from previous shifts. |
| **Empower Clinicians with Cardiac Diagnosis Support** | Delays in cardiac risk assessment and diagnosis support due to the need for human analysis of complex ECG data and patient history. | 1. [Cardiology Agent](agent_bar_v2/subagents/hcls/cardiology_consult/agent.py) | The mission with this agent journey is to assess cardiac risk by analyzing uploaded ECG data and patient history. |

### 💰 Financial Services Industry (FSI)

| Use Case | Problem Statement | Agents Used | Description |
| :--- | :--- | :--- | :--- |
| **Build Winning Portfolios with Holistic Data** | Inefficient investment decision-making due to the difficulty for wealth managers in synthesizing disparate macroeconomic trends and micro-level company performance data. | 1. [Macroeconomic Research Agent](agent_bar_v2/subagents/fsi/holistic_investment_strategy/economics/agent.py)<br>2. [Earnings Call Analytics Agent](agent_bar_v2/subagents/fsi/holistic_investment_strategy/earnings/agent.py)<br>3. [Finsights](agent_bar_v2/subagents/fsi/holistic_investment_strategy/finsights/agent.py) | The mission with this agent journey is to build robust investment portfolios by analyzing macroeconomic data and earnings call transcripts. |
| **De-Risk Complex Legacy Banking migrations to Cloud** | High risk and cost associated with manually migrating complex legacy banking cores and translating proprietary schemas to the cloud. | 1. [Domain Discovery Agent](agent_bar_v2/subagents/fsi/banking_modernization_factory/discovery/agent.py)<br>2. [Oracle To Big query Translation Agent](agent_bar_v2/subagents/fsi/banking_modernization_factory/migration/agent.py) | The mission with this agent journey is to migrate a legacy banking core by scanning legacy code and translating proprietary Oracle schemas to the cloud. |
| **Protect Sensitive Corporate Assets from Breaches** | Slow security threat remediation and high losses due to the manual effort required from SecOps teams to analyze logs and draft reports. | 1. [Cyber Guardian](agent_bar_v2/subagents/fsi/cyber_incident_response/agent.py) | The mission with this agent journey is to mitigate security threats by analyzing system logs for indicators of compromise. |

### 🛒 Retail/CPG

| Use Case | Problem Statement | Agents Used | Description |
| :--- | :--- | :--- | :--- |
| **Achieve Global Marketing Time-to-Market in One Hour** | High creative production costs and long time-to-market for generating localized marketing content for global product launches. | 1. [Product Ad Generation Agent](agent_bar_v2/subagents/retail/global_campaign_manager/sub_agents/product_ad_generation/agent.py)<br>2. [Video Translation Agent](agent_bar_v2/subagents/retail/global_campaign_manager/sub_agents/video_transcription/agent.py) | The mission with this agent journey is to automate the creation of marketing assets by generating video ads and localizing them into different markets. |
| **Democratize Inventory Data Access for Non-Technical Managers** | Data silos and poor product data quality, leading to inefficient inventory management and difficulty accessing operational data. | 1. [Catalog Enrichment Agent](agent_bar_v2/subagents/retail/intelligent_inventory_manager/sub_agents/catalog_enrichment/agent.py)<br>2. [NL2SQL Shopping Assistant](agent_bar_v2/subagents/retail/intelligent_inventory_manager/sub_agents/nl2sql/agent.py) | The mission with this agent journey is to fix product catalogs by uploading raw supplier data and using natural language to query stock levels. |
| **Deflect Low-Level Queries to Improve Customer Satisfaction** | Increased call center volume and customer churn during demand spikes due to inconsistent issue resolution and long wait times. | 1. [Customer Support Agent](agent_bar_v2/subagents/retail/customer_support_hub/sub_agents/customer_support/agent.py)<br>2. [Conversational Shopping Assistant](agent_bar_v2/subagents/retail/customer_support_hub/sub_agents/conversational_shopping_assistant/agent.py) | The mission with this agent journey is to resolve customer service inquiries by routing issues to the correct specialized sub-agents. |

### 🎬 Media

| Use Case | Problem Statement | Agents Used | Description |
| :--- | :--- | :--- | :--- |
| **Unlock Value and Monetize Video Content Archives** | Revenue loss from dormant video libraries due to the high cost and difficulty of manually creating metadata, moderation, and finding highlight clips. | 1. [Video Transcription Agent](agent_bar_v2/subagents/cross_industry/meeting_intelligence/sub_agents/transcription/agent.py)<br>2. [Video Moments Agent](agent_bar_v2/subagents/media/content_archive_engine/sub_agents/video_analysis/agent.py)<br>3. [Video Content Moderation Agent](agent_bar_v2/subagents/media/content_archive_engine/sub_agents/content_moderation/agent.py) | The mission with this agent journey is to monetize video archives by automating transcription, finding viral moments, and ensuring content safety compliance. |
| **Open International Revenue Streams with Subtitles and Dubbing** | Missed revenue in international markets due to the slow pace and high cost of traditional human subtitling and dubbing for streaming content. | 1. [Video Translation Agent](agent_bar_v2/subagents/media/global_content_localizer/sub_agents/translation/agent.py) | The mission with this agent journey is to expand your streaming reach by uploading content and automatically generating subtitles and dubbed audio tracks. |

### ⚔️ Cross-Industry

| Use Case | Problem Statement | Agents Used | Description |
| :--- | :--- | :--- | :--- |
| **Minimize Legal Exposure with Compliant Contract Reviews** | High risk and administrative burden for legal teams manually conducting tedious privacy and risk reviews for every contract. | 1. [Contract Review Agent](agent_bar_v2/subagents/cross_industry/legal_guardian/sub_agents/contract_review/agent.py) | The mission with this agent journey is to safeguard enterprise data by auditing documents for privacy compliance and legal risks. |
| **Increase Sales Velocity with Persuasive Pitch Assets** | Slow sales cycles and inconsistent bid quality because sales teams are manually drafting complex SOWs and pitch sizzle reels. | 1. [Professional Services (PSO) Proposal Writer](agent_bar_v2/subagents/cross_industry/proposal_pitch_factory/sub_agents/proposal_writer/agent.py)<br>2. [Product Ad Generation Agent](agent_bar_v2/subagents/cross_industry/proposal_pitch_factory/sub_agents/product_ad_generation/agent.py) | The mission with this agent journey is to win client deals by having agents draft statements of work and create product "sizzle reels". |
| **Optimize Cloud Resource Efficiency to Save Bills** | Difficulty identifying cloud resource waste and optimizing expensive BigQuery usage, directly impacting the bottom line. | 1. Cloud Cost AI Guru<br>2. BigQuery Optimization Agent | The mission with this agent journey is to cut your cloud bill by having an agent squad identify resource waste and refactor expensive database queries. |
| **Save Administrative Hours with Searchable Corporate Knowledge** | Lost corporate knowledge and low team alignment because critical town hall decisions rely on memory rather than searchable notes. | 1. [Video Transcription Agent](agent_bar_v2/subagents/cross_industry/meeting_intelligence/sub_agents/transcription/agent.py)<br>2. [Video Moments Agent](agent_bar_v2/subagents/cross_industry/meeting_intelligence/sub_agents/video_analysis/agent.py) | The mission with this agent journey is to summarize town hall meetings by automatically capturing audio and identifying key topics and speakers. |
| **Democratize Complex Data Analysis to Reveal Hidden Connections** | Hidden business insights and connections are missed because complex data is siloed across disparate, difficult-to-query databases. | 1. Graph Creation and Natural Language Querying Agent | The mission with this agent journey is to connect disparate databases by having an agent squad automatically build a logical knowledge graph. |
| **Minimize Disruptions by Visualizing Single Points of Failure** | Slow response to disruptions due to the difficulty of visualizing complex supply chain dependencies and identifying single points of failure. | 1. Graph Creation and Natural Language Querying Agent | The mission with this agent journey is to visualize risk by having a graph agent automatically transform raw relationship data into an interactive visual map. |
| **Accelerate Productivity and Onboarding of Engineering New Hires** | Reduced engineering productivity and long onboarding cycles due to the difficulty for new hires in mastering complex cloud console workflows. | 1. Sherpa | The mission with this agent journey is to onboard new hires by guiding them step-by-step through complex technical tasks in the cloud console. |

*Note: Agents without links are planned conceptual models not yet instantiated in the codebase.*


## Setup

For comprehensive setup, infrastructure provisioning (Terraform), and deployment instructions, please follow the [**Setup Guide (setup.md)**](setup.md).

### Quick Start (Local Development)

If you just want to run the agent locally for development:

1. **Prerequisites:**
   - Python 3.10+
   - `pip` or `uv` for dependency management.

2. **Installation:**
   ```bash
   # Create and activate a virtual environment
   python3 -m venv .venv
   source .venv/bin/activate

   # Install the ADK and dependencies
   pip install google-adk
   pip install -e .
   ```

## Testing with the ADK Web UI

The ADK Web UI provides an interactive interface for chatting with the agents. Agent Bar v2 dynamically loads specific sub-agents and prompts based on the session's **industry** and **use case** configuration.

1. **Start the ADK web interface:**
```bash
adk web
```

2. **Initialize the session state:**
Agent Bar v2 relies on the session state to determine which agents to activate. This mapping is defined in `agent_bar_v2/subagents/agent_registry.py`. By changing the `industry_id` and `use_case_id` in the state initialization, you dynamically swap the agents handling the conversation.

In a separate terminal, use `curl` to set the initial context for your session (e.g., cross-industry meeting intelligence):
```bash
curl -X POST http://localhost:8000/apps/agent_bar_v2/users/user/sessions/s_123 \
     -H "Content-Type: application/json" \
     -d '{ "user_id": "123", "industry_id": "cross", "use_case_id": "meeting_intelligence" }'
```

*To explore different use cases, refer to the `INDUSTRY_USE_CASE_AGENTS_MAP` dictionary in `agent_registry.py` for valid `industry_id` and `use_case_id` combinations.*

2.1. **Custom Agents Workflow:**
You can also override the default registry and define custom workflows directly in the state:
```bash
curl -X POST http://localhost:8000/apps/agent_bar_v2/users/user/sessions/s_123 \
     -H "Content-Type: application/json" \
     -d '{  "user_id": "123", "industry_id": "cross", "use_case_id": "legal_guardian", "is_custom": true, "custom_agents": [ "contract_review" ], "custom_workflow_map": { "start": "contract_review", "contract_review": "end" }, "custom_root_instructions": "You are a highly skilled legal assistant..."}'
```

3. **Open the web interface:**
Navigate to the URL containing your specific user ID and session ID:
```text
http://127.0.0.1:8000/dev-ui/?app=agent_bar_v2&session=s_123&userId=user
```

4. **Start Chatting:**
Select the agent and the initialized session in the web UI, and begin your interaction.


# Contributors

[Aadila Jasmin](mailto:aadilajasmin@google.com)

[Aakansha Mehrotra](mailto:maakansha@google.com)

[Agustin Ramírez Hernández](mailto:agusramirez@google.com)

[Ahmad Khan](mailto:ahmadkh@google.com)

[Asish Dhall](mailto:asishdhall@google.com)

[Dhaval Durve](mailto:dhavaldurve@google.com)

[Dola Adesanya](mailto:dolaade@google.com)

[Ian Mckee](mailto:ianmckee@google.com)

[Mike Hilton](mailto:emceehilton@google.com)

[Nivea Rajesh Bekal](mailto:niveabekal@google.com)

[Rob Keohane](mailto:rkeohane@google.com)

[Sean Rastatter](mailto:srastatter@google.com)

[Theo Haddad](mailto:theohaddad@google.com)


# Acknowledgements

AgentSmithy utilized two open source projects to speed up development. We found these resources invaluable and appreciate the teams that built and maintain them. 

1. [Agent Starter Pack](https://github.com/GoogleCloudPlatform/agent-starter-pack)
2. [ADK Samples](https://github.com/google/adk-samples/tree/main)

# Contributing

Contributions are welcome! See the [Contributing Guide](CONTRIBUTING.md).

# Feedback

We value your input! Your feedback helps us improve AgentSmithy and make it more useful for the community.

## Getting Help

If you encounter any issues or have specific suggestions, please first consider [raising an issue](https://github.com/GoogleCloudPlatform/AgentSmithy/issues) on our GitHub repository.

## Share Your Experience

For other types of feedback, or if you'd like to share a positive experience or success story using this, we'd love to hear from you! You can reach out to us at <a href="mailto:agentsmithy-feedback@google.com">agentsmithy-feedback@google.com</a>.

Thank you for your contributions!

# Relevant Terms of Service

[Google Cloud Platform TOS](https://cloud.google.com/terms)

[Google Cloud Privacy Notice](https://cloud.google.com/terms/cloud-privacy-notice)


# Responsible Use

Building and deploying generative AI agents requires a commitment to responsible development practices. AgentSmithy provides the you the tools to build agents, but you must also provide the commitment to ethical and fair use of these agents. We encourage you to:

*   **Start with a Risk Assessment:** Before deploying your agent, identify potential risks related to bias, privacy, safety, and accuracy.
*   **Implement Monitoring and Evaluation:** Continuously monitor your agent's performance and gather user feedback.
*   **Iterate and Improve:**  Use monitoring data and user feedback to identify areas for improvement and update your agent's prompts and configuration.
*   **Stay Informed:**  The field of AI ethics is constantly evolving. Stay up-to-date on best practices and emerging guidelines.
*   **Document Your Process:**  Maintain detailed records of your development process, including data sources, models, configurations, and mitigation strategies.

# Disclaimer

**This is not an officially supported Google product.**

Copyright 2026 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0
