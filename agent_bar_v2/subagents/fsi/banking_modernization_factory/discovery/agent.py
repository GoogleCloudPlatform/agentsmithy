from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.genai import types

from .prompt import INSTRUCTION_PROMPT
from .tools.repo_analysis_tool import RepoAnalysisTools

AGENT_DESCRIPTION = "Analyzes legacy codebases via GitHub repositories to identify business domains, logic, and dependencies for modernization."

# Initialize the custom tool class
tools_instance = RepoAnalysisTools()

tools = [
    FunctionTool(func=tools_instance.list_repository_files),
    FunctionTool(func=tools_instance.get_file_content),
]


# Model configuration
GEMINI_MODEL_CONFIG = Gemini(
    model="gemini-2.5-flash",
    generation_config=types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=65536,
    ),
    name="domain_discovery",
    description=AGENT_DESCRIPTION,
    instruction=INSTRUCTION_PROMPT,
    tools=tools,
)
