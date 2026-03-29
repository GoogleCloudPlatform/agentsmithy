from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.genai import types

from .prompt import INSTRUCTION_PROMPT
from .tools.repo_analysis_tool import RepoAnalysisTools

# Initialize the custom tool class
tools_instance = RepoAnalysisTools()

tools = [
    FunctionTool(func=tools_instance.list_repository_files),
    FunctionTool(func=tools_instance.get_file_content),
]

AGENT_NAME = "discovery_agent"
AGENT_DESCRIPTION = "Analyzes legacy codebases via GitHub repositories to identify business domains, logic, and dependencies for modernization."

# Model configuration
root_agent = LlmAgent(
    model="gemini-2.5-flash",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=65536,
    ),
    name=AGENT_NAME,
    description=AGENT_DESCRIPTION,
    instruction=INSTRUCTION_PROMPT,
    tools=tools,
)
