import requests
import json
import vertexai
from vertexai.generative_models import GenerativeModel, Part

from agent_bar_v2.subagents.agent_registry import INDUSTRY_USE_CASE_AGENTS_MAP

# Prompts
from agent_bar_v2.subagents.cross_industry.meeting_intelligence.prompts import SYSTEM_INSTRUCTION as CROSSIN_MEETING_INTELLIGENCE_PROMPT
from agent_bar_v2.subagents.cross_industry.legal_guardian.prompts import SYSTEM_INSTRUCTION as CROSSIN_LEGAL_GUARDIAN_PROMPT
from agent_bar_v2.subagents.cross_industry.proposal_pitch_factory.prompts import SYSTEM_INSTRUCTION as CROSSIN_PROPOSAL_PITCH_FACTORY_PROMPT
from agent_bar_v2.subagents.fsi.holistic_investment_strategy.prompts import SYSTEM_INSTRUCTION as HOLISTIC_INVESTMENT_STRATEGY_PROMPT
from agent_bar_v2.subagents.fsi.banking_modernization_factory.prompts import SYSTEM_INSTRUCTION as BANKING_MODERNIZATION_FACTORY_PROMPT
from agent_bar_v2.subagents.retail.global_campaign_manager.prompts import SYSTEM_INSTRUCTION as GLOBAL_CAMPAIGN_LAUNCHER_PROMPT
from agent_bar_v2.subagents.retail.customer_support_hub.prompts import SYSTEM_INSTRUCTION as CUSTOMER_SUPPORT_HUB_PROMPT
from agent_bar_v2.subagents.media.global_content_localizer.prompts import SYSTEM_INSTRUCTION as GLOBAL_CONTENT_LOCALIZER_PROMPT
from agent_bar_v2.subagents.industry_prompts import (
    DEFAULT_PROMPT,
    HCLS_CLINICAL_HANDOVER_PROMPT,
    HCLS_RESEARCH_ACCELERATOR_PROMPT,
    MEDIA_CONTENT_ARCHIVE_ENGINE_PROMPT,
    HCLS_PROVIDER_SEARCH_AGENT_PROMPT,
    HCLS_CARDIOLOGY_CONSULT_COPILOT_PROMPT,
    CYBER_INCIDENT_RESPONSE_PROMPT
)

# Initialize Vertex AI
vertexai.init(project="ai-agent-bar-2026-stage", location="us-central1")
model = GenerativeModel("gemini-2.5-flash")

# Industries and their use cases
industry_use_cases = {
    "hcls": "research_accelerator provider_search_agent clinical_handover cardiology_consult_copilot",
    "fsi": "holistic_investment_strategy banking_modernization_factory cyber_incident_response",
    "retail": "global_campaign_launcher customer_support_hub",
    "media": "content_archive_engine global_content_localizer",
    "cross": "legal_guardian proposal_pitch_factory meeting_intelligence",
}

BASE_URL = "http://localhost:8000"
APP_NAME = "agent_bar_v2"
USER_ID = "123"
SESSION_ID = "s_123"

def delete_session():
    """Deletes the session."""
    print("Deleting session...")
    url = f"{BASE_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions/{SESSION_ID}"
    try:
        requests.delete(url)
    except requests.exceptions.RequestException as e:
        print(f"Could not delete session: {e}")


def create_session(industry, use_case):
    """Creates a new session."""
    print("Creating session...")
    url = f"{BASE_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions/{SESSION_ID}"
    headers = {"Content-Type": "application/json"}
    data = {"industry_id": industry, "use_case_id": use_case}
    try:
        requests.post(url, headers=headers, data=json.dumps(data))
    except requests.exceptions.RequestException as e:
        print(f"Could not create session: {e}")


def verify_with_gemini(system_prompt, agent_response):
    """Verifies the agent's response against the system prompt using Gemini."""
    print("Verifying with Gemini...")
    prompt = f"""You are a helpful assistant that evaluates if an AI agent's response aligns with its designated persona and capabilities described in a system prompt.

**System Prompt:**
---
{system_prompt}
---

**Agent Response:**
---
{agent_response}
---

Does the agent's response accurately reflect the persona and capabilities described in the system prompt? Please answer with 'Yes' or 'No' and provide a brief explanation for your answer."""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error during Gemini verification: {e}"


def ask_question(expected_prompt):
    """Asks a generic question to the agent and returns the results."""
    print("Asking question...")
    url = f"{BASE_URL}/run"
    headers = {"Content-Type": "application/json"}
    data = {
        "appName": APP_NAME,
        "userId": USER_ID,
        "sessionId": SESSION_ID,
        "newMessage": {
            "role": "user",
            "parts": [{"text": "Hello, agent! Please tell me about your capabilities."}]
        },
    }

    result = {
        "expected_prompt": expected_prompt,
        "agent_response": "",
        "gemini_verification": ""
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"Response Status Code: {response.status_code}")

        try:
            response_json = response.json()
            
            actual_response_text = ""
            if response_json and isinstance(response_json, list):
                first_event = response_json[0]
                content = first_event.get("content", {})
                parts = content.get("parts", [])
                if parts and isinstance(parts, list):
                    actual_response_text = parts[0].get("text", "")
            
            result["agent_response"] = actual_response_text

            print("--- SYSTEM PROMPT ---")
            print(expected_prompt)
            print("--- AGENT RESPONSE ---")
            print(actual_response_text)
            print("----------------------")

            if not actual_response_text:
                print("VERIFICATION FAILED: Agent returned an empty response.")
                result["gemini_verification"] = "VERIFICATION FAILED: Agent returned an empty response."
            else:
                verification_result = verify_with_gemini(expected_prompt, actual_response_text)
                result["gemini_verification"] = verification_result
                print("--- GEMINI VERIFICATION ---")
                print(verification_result)
                print("---------------------------")

        except json.JSONDecodeError:
            error_message = f"Error: Failed to decode JSON from response. Response text: {response.text}"
            print(error_message)
            result["gemini_verification"] = error_message

    except requests.exceptions.RequestException as e:
        error_message = f"Failed to get response from agent: {e}"
        print(error_message)
        result["gemini_verification"] = error_message
    
    return result


def main():
    """Main function to run the tests."""
    all_results = []
    for industry, use_cases in industry_use_cases.items():
        for use_case in use_cases.split():
            print(f"Testing Industry: {industry}, Use Case: {use_case}")
            delete_session()
            create_session(industry, use_case)
            
            expected_prompt = INDUSTRY_USE_CASE_AGENTS_MAP.get(industry, {}).get(use_case, {}).get("prompt", "")
            
            test_result = ask_question(expected_prompt)
            test_result["industry"] = industry
            test_result["use_case"] = use_case
            all_results.append(test_result)
            print("\n")

    with open("test_results.json", "w") as f:
        json.dump(all_results, f, indent=4)
    print("Results saved to test_results.json")

if __name__ == "__main__":
    main()
