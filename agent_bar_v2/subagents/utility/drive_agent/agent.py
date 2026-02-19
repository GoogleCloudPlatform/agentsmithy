from google.adk.agents import Agent
from .prompt import PROMPT
from .tools import copy_and_replace_document_tool, save_document_tool, list_drive_documents_tool


drive_agent = Agent(
    name="DriveAgent",
    model="gemini-2.5-flash",
    description="Drive Agent",
    instruction=PROMPT,
    tools=[
          copy_and_replace_document_tool,
          save_document_tool,
          list_drive_documents_tool,
    ],
)