import os
from dotenv import load_dotenv
from google import genai
from agent_bar_v2.subagents.agent_registry import get_agent_descriptions_json

# Load the environment variables to pick up GEMINI_API_KEY if available
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

def generate_custom_root_instructions(user_vision: str, selected_agent_ids: list[str]) -> str:
    """
    Generates custom root agent instructions using Gemini based on the user's vision 
    and the selected sub-agents' descriptions.
    """
    # 1. Get the sub-agent descriptions in JSON format
    agent_descriptions = get_agent_descriptions_json(selected_agent_ids)
    
    # 2. Construct the prompt
    prompt = f"""
You are an expert multi-agent orchestrator designer. 
A user has provided a vision for a custom workflow and selected a set of specialized sub-agents.
Your goal is to write a cohesive system instruction for the "Root Agent" that will orchestrate these sub-agents to achieve the user's vision.

User's Vision/Task Description:
{user_vision}

Selected Sub-Agents Available (JSON):
{agent_descriptions}

Task: Output ONLY the system instructions for the Root Agent as a single paragraph. 
Do not include any conversational text, markdown formatting blocks, or explanations. Just the final instructions text.

Example format: "You are a highly skilled legal assistant specializing in contract analysis. Your goal is to identify potential risks, clarify complex terminology, and ensure compliance with standard regulatory frameworks. You have access to specialized agents to assist you in this task. Please provide concise, actionable feedback for each document reviewed."
"""

    # 3. Call the Gemini API using the new GenAI SDK
    client = genai.Client() # This will automatically pick up GEMINI_API_KEY from the environment
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    
    # Strip any extra whitespace and return
    return response.text.strip()

if __name__ == "__main__":
    # Test case matching the README example idea
    sample_vision = "I want to create a workflow where a user uploads a new business contract, and we review it to ensure it avoids high financial risk and conforms to local laws."
    sample_agents = ["contract_review"]
    
    print("Generating custom instructions for the Root Agent...\n")
    
    instructions = generate_custom_root_instructions(
        user_vision=sample_vision, 
        selected_agent_ids=sample_agents
    )
    
    print("--- GENERATED INSTRUCTIONS ---")
    print(instructions)
