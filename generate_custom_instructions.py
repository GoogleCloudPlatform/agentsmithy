import os
from dotenv import load_dotenv
from google import genai
from agent_bar_v2.subagents.agent_registry import get_agent_descriptions_json

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

def generate_custom_root_instructions(user_vision: str, selected_agent_ids: list[str]) -> str:
    """
    Generates custom root agent instructions using Gemini based on the user's vision 
    and the selected sub-agents' descriptions.
    """
    agent_descriptions = get_agent_descriptions_json(selected_agent_ids)
    workflow_sequence = " -> ".join(selected_agent_ids)

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
        model="gemini-2.5-flash",
        contents=prompt,
    )
    
    return response.text.strip()

if __name__ == "__main__":
    sample_vision = "Research complex medical conditions and generate visual storyboard/media assets for patient education campaigns."
    sample_agents = ["medical_search_agent", "product_ad_generation"]
    
    print("Generating custom instructions for the Root Agent...\n")
    
    instructions = generate_custom_root_instructions(
        user_vision=sample_vision, 
        selected_agent_ids=sample_agents
    )
    
    print("--- GENERATED INSTRUCTIONS ---")
    print(instructions)
