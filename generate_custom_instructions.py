import os
from dotenv import load_dotenv
from google import genai
import json
from agent_bar_v2.subagents.agent_registry import get_agent_descriptions_json, AGENT_REGISTRY_MAP

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

def generate_custom_root_instructions(user_vision: str, selected_agent_ids: list[str]) -> str:
    """
    Generates custom root agent instructions using Gemini based on the user's vision 
    and the selected sub-agents' descriptions.
    """
    agent_descriptions = get_agent_descriptions_json(selected_agent_ids)
    workflow_sequence = " -> ".join(selected_agent_ids)
    print("AGENT DESCRIPTIONS")
    print(agent_descriptions)

    prompt = f"""
You are an expert multi-agent orchestrator designer. 
A user has provided a vision for a custom workflow and selected a set of specialized sub-agents.
Crucially, these sub-agents represent a specific, sequential workflow that the Root Agent must follow.

Sequential Workflow Order:
{workflow_sequence}

User's Vision/Task Description:
{user_vision}

Selected Sub-Agents Available (JSON):
{agent_descriptions}

Your goal is to write a cohesive system instruction for the "Root Agent" that will orchestrate these sub-agents to achieve the user's vision.
The generated instruction MUST use clear markdown formatting to provide a structured system prompt. It must include a persona, the available agents, the step-by-step sequential workflow, and basic error handling.

Task: Output ONLY the generated system instructions for the Root Agent. Do not include any conversational text or explanations. Just the final system prompt.

Use the following exact markdown structure for your output:

You are an expert [Specific Persona based on vision]. Your tone should be [Tone, e.g., authoritative, polite].

### Your Mission
[High-level goal based on the user's vision]

### Available Sub-Agents
[For each agent in the JSON, provide a numbered list with the agent name and a specific instruction on when/how the Root Agent should use it.]

### Sequential Workflow
[Provide a numbered list dictating the exact step-by-step workflow the Root Agent must follow, strictly adhering to the Sequential Workflow Order provided above. Explicitly state which agent is used at each step.]

### Interactive Routing & Handoff Rules
- You are an interactive orchestrator, not a silent executor. If a sub-agent asks the user for approval, requires confirmation, or asks a question (like "Do you approve this script?"), you MUST halt horizontal progression and relay that EXACT question to the user.
- Wait for the user to respond, and then call that SAME sub-agent again with the user's feedback.
- Do NOT proceed to the next agent in the sequence until the current agent's conversational loop is completely finished.

### Error Handling & Rules
- If a sub-agent fails, encounters an error, or returns missing data, [insert logical fallback behavior].
- Always ensure [insert key priority based on vision].
"""

    project_id = os.getenv("PROJECT_ID")
    location = os.getenv("LOCATION", "us-central1")
    client = genai.Client(vertexai=True, project=project_id, location=location)
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview"),
        contents=prompt,
    )
    
    return response.text.strip()

def select_agents_for_vision(user_vision: str) -> dict:
    """
    Evaluates the user's vision against all available agents
    and returns a structured JSON payload predicting the required agents and their workflow map.
    """
    all_agent_ids = list(AGENT_REGISTRY_MAP.keys())
    agent_descriptions = get_agent_descriptions_json(all_agent_ids)
    
    prompt = f"""
    You are an expert System Architect for a multi-agent framework.
    A user has provided a vision for an agentic system they want to build.
    Your job is to evaluate if this vision can be accomplished using the available sub-agents.
    
    User's Vision/Task Description:
    {user_vision}
    
    All Available Sub-Agents:
    {agent_descriptions}
    Evaluate the vision. If it is possible, select the explicitly required agents from the available list.
    Do not invent new agent IDs; **only** use the ones provided in the JSON list.

    OUTPUT FORMAT: You MUST output a raw JSON object string with no markdown formatting. The JSON MUST perfectly match this exact structure:
    {{
      "is_possible": true,
      "reason": "Explain why it is possible or not.",
      "selected_agent_ids": ["agent_1", "agent_2"],
      "workflow_map": {{
        "start": "agent_1",
        "agent_1": "agent_2",
        "agent_2": "end"
      }}
    }}
    
    CRUCIAL RULES FOR `workflow_map`:
    - You MUST populate the `workflow_map` object using the EXACT IDs you placed in the `selected_agent_ids` array. Do not leave it empty!
    - The first key must be "start" mapping to the first agent ID.
    - Each agent ID must map to the next agent ID in the sequence.
    - The final agent ID must map to the string "end".
    """
    
    project_id = os.getenv("PROJECT_ID")
    location = os.getenv("LOCATION", "us-central1")
    client = genai.Client(vertexai=True, project=project_id, location=location)
    
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview"),
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )
    
    return json.loads(response.text)

def build_custom_workflow(user_vision: str) -> dict:
    """
    Main orchestrator wrapper that executes the two steps for user vision + custom root prompt instructions.
    """
    selection = select_agents_for_vision(user_vision)
    
    if not selection.get("is_possible"):
        return {"success": False, "reason": selection.get("reason")}
        
    selected_agent_ids = selection.get("selected_agent_ids", [])
    if not selected_agent_ids:
        return {"success": False, "reason": "No agents were selected despite being marked as possible."}
        
    root_instructions = generate_custom_root_instructions(
        user_vision=user_vision, 
        selected_agent_ids=selected_agent_ids
    )
    
    return {
        "success": True,
        "is_custom": True,
        "custom_agents": selected_agent_ids,
        "custom_workflow_map": selection.get("workflow_map", {}),
        "custom_root_instructions": root_instructions
    }


if __name__ == "__main__":
    sample_vision = "Research complex medical conditions and generate visual storyboard/media assets for patient education campaigns."
    
    print(f"Executing Full End-to-End Pipeline for vision:\\n{sample_vision}\\n")
    
    import json
    workflow_payload = build_custom_workflow(user_vision=sample_vision)
    
    print("--- FINAL JSON PAYLOAD FOR FRONTEND ---")
    print(json.dumps(workflow_payload, indent=2))
