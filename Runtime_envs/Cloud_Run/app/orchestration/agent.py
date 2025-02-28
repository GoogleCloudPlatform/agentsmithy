# ==============================================================================
# Copyright 2025 Google LLC. This software is provided as-is, without warranty
# or representation for any use or purpose. Your use of it is subject to your
# agreement with Google.
# ==============================================================================

"""Module used to define and interact with agent orchestrators."""

import asyncio
from typing import AsyncGenerator, Dict, Any

from langchain_core.messages import AIMessageChunk, ToolMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from vertexai.generative_models import ResponseValidationError
from vertexai.preview import reasoning_engines

from app.orchestration.constants import GEMINI_FLASH_20_LATEST
from app.orchestration.enums import (
    IndustryType,
    OrchestrationFramework
)
from app.orchestration.tools import get_tools
from app.orchestration.models import get_model_obj_from_string
from app.utils.output_types import OnChatModelStreamEvent, ChatModelStreamData


class AgentManager():
    """Class that constructs and manages an Agent Executor"""

    def __init__(
        self,
        prompt: str,
        industry_type: str = IndustryType.FINANCE_INDUSTRY.value,
        orchestration_framework: str = OrchestrationFramework.LANGCHAIN_REACT_AGENT.value,
        model_name: str = GEMINI_FLASH_20_LATEST,
        return_steps: bool = False,
        verbose: bool = True):
        """Constructs a custom agent with the specified configuration.

        Args:
            prompt: System instructions to give to the agent.
            industry_type: The agent industry type to use. Correlates to tool configs.
            orchestration_framework: The type of agent framework to use.
            model_name: The name of the LLM to use for the  agent.
            return_steps: Whether to return the agent's trajectory of intermediate
                steps at the end in addition to the final output.
            verbose: Whether or not run in verbose mode. In verbose mode, some intermediate
                logs will be printed to the console.
        """
        self.prompt = prompt
        self.tools = get_tools(industry_type)
        self.model_name = model_name
        self.model_obj = get_model_obj_from_string(self.model_name)

        if orchestration_framework == OrchestrationFramework.LANGCHAIN_REACT_AGENT.value:
            self.agent_executor = create_react_agent(
                prompt=self.prompt,
                model=self.model_obj,
                tools=self.tools,
                debug=verbose
            )
        # TODO: this needs work - will not be compatible with the below astream function
        elif orchestration_framework == OrchestrationFramework.VERTEX_AI_REASONING_ENGINE_LANCHAIN_AGENT.value:
            self.agent_executor = reasoning_engines.LangchainAgent(
                prompt=self.prompt,
                model=self.model_name,
                model_kwargs={'temperature': 0},
                tools=self.tools,
                agent_executor_kwargs={'return_intermediate_steps': return_steps}
            )
        else:
            raise ValueError(f'Orchestration Framework {orchestration_framework} is not currently supported.')


    async def astream(
        self,
        input: Dict[str, Any],
        max_retries: int = 10,
    ) -> AsyncGenerator[Dict, Any]:
        """Asynchronously event streams the Agent output.

        Args:
            agent_executor: The agent executor instance.
            prompt: The end-user question that was asked.
            session_id: The session id.
            max_retries: Max number of retries if a ResponseValidationError is encountered.

        Yields:
            Dictionaries representing the streamed agent output.
        """
        for attempt in range(max_retries):
            try:
                async for chunk in self.agent_executor.astream(input, stream_mode="messages"):
                    message = chunk[0]
                    if isinstance(message, (AIMessageChunk, AIMessage)):
                        stream_data = ChatModelStreamData(chunk=message)
                        yield OnChatModelStreamEvent(data=stream_data)
                    elif isinstance(message, ToolMessage):
                        # TODO: Implement something like this:
                        # stream_data = ToolMessageStreamData(tool_call_id=message.tool_call_id, result=message.content)
                        # yield OnToolMessageStreamEvent(data=stream_data)
                        print(f"ToolMessage received: {message.content}")
                        continue

                return  # Exit the loop if successful
            except ResponseValidationError as e:
                print(f"Issue encountered: {e} - Attempt {attempt + 1} of {max_retries}")
                await asyncio.sleep(1)  # Add a small delay before retrying
                continue  # Retry
            except Exception as e:
                print(f"Unexpected error: {e}")
                raise

        # If all retries fail
        raise Exception("Max retries reached, please check your prompt before trying again.")
