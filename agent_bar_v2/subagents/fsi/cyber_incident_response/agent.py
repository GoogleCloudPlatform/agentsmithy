from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from .prompt import SYSTEM_INSTRUCTIONS
from .log_scanner.agent import root_agent as log_scanner_agent

AGENT_DESCRIPTION = "Orchestrates cyber incident response by scanning logs, analyzing threats, and drafting incident reports."


def get_incident_contacts() -> list[dict]:
    """
    Returns a list of critical contacts for cyber incident response.
    """
    return [
        {"role": "CISO", "name": "Sarah Connor", "email": "sarah.connor@example.com", "phone": "+1-555-0100"},
        {"role": "Legal Counsel", "name": "Atticus Finch", "email": "atticus.finch@example.com", "phone": "+1-555-0101"},
        {"role": "PR/Comms", "name": "Don Draper", "email": "don.draper@example.com", "phone": "+1-555-0102"},
        {"role": "Cloud Provider Support", "name": "Tech Giant Corp", "email": "support@cloudprovider.com", "phone": "+1-800-555-0199"},
    ]


def get_impacted_systems() -> list[dict]:
    """
    Returns a list of critical systems that could be impacted by a cyber incident.
    """
    return [
        {"system": "Core Banking System", "owner": "John Doe", "email": "john.doe@example.com", "criticality": "High"},
        {"system": "Customer Portal", "owner": "Jane Smith", "email": "jane.smith@example.com", "criticality": "Medium"},
        {"system": "Trading Platform", "owner": "Bob Jones", "email": "bob.jones@example.com", "criticality": "High"},
        {"system": "Employee Payroll", "owner": "Alice Brown", "email": "alice.brown@example.com", "criticality": "Low"},
    ]

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=65536,
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ],
    ),
    name="cyber_incident_response",
    description=AGENT_DESCRIPTION,
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[
        AgentTool(log_scanner_agent),
        get_incident_contacts,
        get_impacted_systems,
    ],
)
