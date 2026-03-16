from google.adk.agents import LlmAgent
from injector import Injector
from ...configuration import AgentConfig

def get_answer_generation_agent(injector: Injector) -> LlmAgent:
    config = injector.get(AgentConfig)
    
    instruction = """
You are a helpful Macroeconomic Assistant. Provide a clear, technical, and data-driven 
answer to the user's question based on the JSON data retrieved from the database.

**Role:** Macroeconomic Researcher.
**Constraint:** Base your analysis ONLY on the provided data. If the data is empty or irrelevant, state that clearly.
**Format:** Provide a concise executive summary followed by key data points.
"""

    return LlmAgent(
        model="gemini-2.5-flash",
        name="AnswerGenerationAgent",
        description="Synthesizes SQL query results into a human-readable macroeconomic answer.",
        instruction=instruction,
    )
