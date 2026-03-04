import json
from google.adk.agents import LlmAgent
from google.genai import types


from .prompt import SYSTEM_INSTRUCTIONS
from .mock_logs import MOCK_LOGS

AGENT_DESCRIPTION = "Scans and analyzes network logs to identify security threats and anomalies."


def get_logs(filter_ip: str = None) -> str:
    """
    Retrieves network logs, optionally filtering by source or destination IP.
    
    Args:
        filter_ip: Optional IP address to filter logs by.
        
    Returns:
        JSON string of filtered logs.
    """
    if filter_ip:
        filtered_logs = [
            log for log in MOCK_LOGS 
            if log.get("source_ip") == filter_ip or log.get("destination_ip") == filter_ip
        ]
        return json.dumps(filtered_logs, indent=2)
    return json.dumps(MOCK_LOGS, indent=2)


def get_unique_ips() -> str:
    """
    Retrieves a list of all unique IP addresses found in the logs.

    Returns:
        JSON string of unique IP addresses.
    """
    ips = set()
    for log in MOCK_LOGS:
        if "source_ip" in log:
            ips.add(log["source_ip"])
        if "destination_ip" in log:
            ips.add(log["destination_ip"])
    return json.dumps(list(ips), indent=2)

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
    name="log_scanner",
    description=AGENT_DESCRIPTION,
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[get_logs, get_unique_ips],
)
