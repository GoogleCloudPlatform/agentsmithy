# ==============================================================================
# Copyright 2025 Google LLC. This software is provided as-is, without warranty
# or representation for any use or purpose. Your use of it is subject to your
# agreement with Google.
# ==============================================================================

"""Module used to define and interact with agent orchestrators."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Iterable

from google.api_core import exceptions
from langchain.agents import (
    AgentExecutor,
    create_react_agent as langchain_create_react_agent
)
from langchain_core.messages import AIMessageChunk, ToolMessage, AIMessage
from langchain_google_vertexai import ChatVertexAI
from langgraph.prebuilt import create_react_agent as langgraph_create_react_agent
from vertexai.preview import reasoning_engines # TODO: update this when it becomes agent engine

from app.orchestration.constants import (
    GEMINI_FLASH_20_LATEST,
)
from app.orchestration.config import (
    USER_AGENT,
    AGENT_DESCRIPTION
)
from app.orchestration.enums import OrchestrationFramework
from app.orchestration.tools import get_tools
from app.utils.utils import get_requirements_from_toml


class BaseAgentManager(ABC):
    """
    Abstract base class for Agent Managers.  Defines the common interface
    for creating and managing agent executors with different orchestration
    frameworks.
    """

    def __init__(
        self,
        prompt: str,
        industry_type: str,
        orchestration_framework: str,
        model_name: str,
        max_retries: int,
        max_output_tokens: int,
        temperature: float,
        top_p: float,
        top_k: int,
        return_steps: bool,
        verbose: bool
    ):
        """
        Initializes the BaseAgentManager with common configurations.

        Args:
            prompt: System instructions to give to the agent.
            industry_type: The agent industry type to use. Correlates to tool configs.
            orchestration_framework: The type of agent framework to use.
            model_name: The valid name of the LLM to use for the agent.
            max_retries: Maximum number of times to retry the query on a failure.
            max_output_tokens: Maximum amount of text output from one prompt.
            temperature: Temperature to use for the agent.
            top_p: Top p value. Chooses the words based on a cumulative probability threshold.
            top_k: Top k value. Chooses the top k most likely words
            return_steps: Whether to return the agent's trajectory of intermediate
                steps at the end in addition to the final output.
            verbose: Whether or not run in verbose mode.
        """
        self.prompt = prompt
        self.industry_type = industry_type
        self.orchestration_framework = orchestration_framework
        self.model_name = model_name
        self.max_retries = max_retries
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.return_steps = return_steps
        self.verbose = verbose

        self.tools = self.get_tools()
        self.model_obj = self.get_model_obj()
        self.agent_executor = self.set_up()


    @abstractmethod
    def set_up(self):
        """
        Abstract method to create the specific agent executor based on the
        orchestration framework.  This must be implemented by subclasses.

        Returns:
            The initialized agent executor instance.
        """
        pass


    def get_tools(self):
        """
        Helper method to retrieve tools based on the industry type.

        Returns:
            A list of tools for the agent to use, based on the industry type.
        """
        return get_tools(
            self.industry_type,
            self.orchestration_framework
        )


    def get_model_obj(self):
        """
        Helper method to retrieve the model object based on the model name 
        and config.

        Returns:
            An LLM object for the Agent to use.

        Exception:
            The model_name is not found.
        """
        try:
            return ChatVertexAI(
                model_name=self.model_name,
                max_retries=self.max_retries,
                max_output_tokens=self.max_output_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                verbose=self.verbose
            )
        except exceptions.NotFound as e:
            raise exceptions.NotFound(f"Resource not found. {e}")
        except Exception as e:
            raise RuntimeError(f"Error encountered initalizing model resource. {e}") from e


    @abstractmethod
    def stream_query(
        self,
        input: Dict[str, Any],
    ) -> Iterable:
        """
        Abstract method to asynchronously stream the Agent output.
        This should be implemented by subclasses to handle the specific
        streaming logic of their agent executor.
        """
        pass


class LangChainPrebuiltAgentManager(BaseAgentManager):
    """
    AgentManager subclass for LangChain Agent orchestration.
    """
    def __init__(
        self,
        prompt: str,
        industry_type: str,
        model_name: Optional[str] = GEMINI_FLASH_20_LATEST,
        max_retries: Optional[int] = 6,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = 0,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        return_steps: Optional[bool] = False,
        verbose: Optional[bool] = True
    ):
        super().__init__(
            prompt=prompt,
            industry_type=industry_type,
            orchestration_framework=OrchestrationFramework.LANGCHAIN_PREBUILT_AGENT.value,
            model_name=model_name,
            max_retries=max_retries,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            return_steps=return_steps,
            verbose=verbose
        )


    def set_up(self):
        """
        Creates a Langchain React Agent executor.
        """
        react_agent = langchain_create_react_agent(
            prompt=self.prompt,
            llm=self.model_obj,
            tools=self.tools,
        )
        return AgentExecutor(
            agent=react_agent,
            tools=self.tools,
            return_intermediate_steps=self.return_steps,
            verbose=self.verbose
        )


    def stream_query(
        self,
        input: Dict[str, Any],
    ) -> Iterable:
        """Event streams the Agent output.

        Args:
            input: The list of messages to send to the model as input.

        Yields:
            Iterable representing the streamed agent output.

        Exception:
            An error is encountered during streaming.
        """
        try:
            for chunk in self.agent_executor.stream(
                {
                    "input": input["messages"][0],
                    "chat_history": input["messages"][1:],
                }
            ):
                if "output" in chunk:
                    chunk["content"] = chunk["output"]
                    yield chunk
        except Exception as e:
            raise RuntimeError(f"Unexpected error. {e}") from e


class LangGraphPrebuiltAgentManager(BaseAgentManager):
    """
    AgentManager subclass for LangGraph Agent orchestration.
    """
    def __init__(
        self,
        prompt: str,
        industry_type: str,
        model_name: Optional[str] = GEMINI_FLASH_20_LATEST,
        max_retries: Optional[int] = 6,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = 0,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        return_steps: Optional[bool] = False,
        verbose: Optional[bool] = True
    ):
        super().__init__(
            prompt=prompt,
            industry_type=industry_type,
            orchestration_framework=OrchestrationFramework.LANGGRAPH_PREBUILT_AGENT.value,
            model_name=model_name,
            max_retries=max_retries,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            return_steps=return_steps,
            verbose=verbose
        )


    def set_up(self):
        """
        Creates a LangGraph Agent executor.
        """
        return langgraph_create_react_agent(
            prompt=self.prompt,
            model=self.model_obj,
            tools=self.tools,
            debug=self.verbose
        )


    def stream_query(
        self,
        input: Dict[str, Any],
    ) -> Iterable:
        """Asynchronously event streams the Agent output.

        Args:
            input: The list of messages to send to the model as input.

        Yields:
            Iterable representing the streamed agent output.

        Exception:
            An error is encountered during streaming.
        """
        try:
            for chunk in self.agent_executor.stream(input, stream_mode="messages"):
                message = chunk[0]
                if isinstance(message, (AIMessageChunk, AIMessage)):
                    yield message
                elif isinstance(message, ToolMessage):
                    # TODO: Implement something like this:
                    # stream_data = ToolMessageStreamData(tool_call_id=message.tool_call_id, result=message.content)
                    # yield OnToolMessageStreamEvent(data=stream_data)
                    print(f"ToolMessage received: {message.content}")
                    continue
            return  # Exit the loop if successful
        except Exception as e:
            raise RuntimeError(f"Unexpected error. {e}") from e


def deploy_agent_to_reasoning_engine(
    agent_manager: BaseAgentManager
) -> reasoning_engines.ReasoningEngine:
    """
    Deploys the Vertex AI reasoning engine to a remote managed endpoint.

    Args:
        agent_manager: The agent_manager to be deployed to reasoning engine.

    Returns:
        Remote Reasoning Engine agent.

    Exception:
        An error is encountered during deployment.
    """
    try:
        remote_agent = reasoning_engines.ReasoningEngine.create(
            agent_manager,
            requirements=get_requirements_from_toml(),
            display_name=USER_AGENT,
            description=AGENT_DESCRIPTION,
            extra_packages=["./app", "./deployment/env"],
        )
    except Exception as e:
        raise RuntimeError(f"Error deploying Reasoning Engine Agent. {e}") from e

    return remote_agent

# class LangGraphCustomAgentManager(BaseAgentManager):
