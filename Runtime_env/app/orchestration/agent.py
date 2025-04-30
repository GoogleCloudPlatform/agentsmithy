# Copyright 2025 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# pylint: disable=C0301, W0107, W0107, W0622, R0917
"""Module used to define and interact with agent orchestrators."""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Generator, Dict, Any, Optional
import uuid

from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService, VertexAiSessionService
from google.adk.runners import Runner
from google.genai import types

from google.api_core import exceptions
from langchain.agents import (
    AgentExecutor,
    create_react_agent as langchain_create_react_agent
)
from langchain_core.messages import  AIMessage
from langchain_google_vertexai import ChatVertexAI
from langchain_google_vertexai.model_garden import ChatAnthropicVertex
from langgraph.prebuilt import create_react_agent as langgraph_create_react_agent
from vertexai.preview import reasoning_engines # TODO: update this when it becomes agent engine

# LlamaIndex
from llama_index.core import Settings
from llama_index.core.agent import ReActAgent
from llama_index.llms.langchain import LangChainLLM

from app.orchestration.constants import GEMINI_FLASH_20_LATEST
from app.orchestration.enums import OrchestrationFramework
from app.orchestration.tools import (
    get_tools,
    get_llamaindex_tools
)


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
        location: str,
        orchestration_framework: str,
        agent_engine_resource_id: str,
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
            location: The GCP location to run the chat model.
            orchestration_framework: The type of agent framework to use.
            agent_engine_resource_id: The Resource ID of the deployed AE Agent (if using AE).
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
        self.location = location
        self.orchestration_framework = orchestration_framework
        self.agent_engine_resource_id = agent_engine_resource_id
        self.model_name = model_name
        self.max_retries = max_retries
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.return_steps = return_steps
        self.verbose = verbose

        self.model_obj = self.get_model_obj()
        self.tools = self.get_tools()
        self.agent_executor = self.create_agent_executor()


    @abstractmethod
    def create_agent_executor(self):
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
            if "claude" in self.model_name:
                return ChatAnthropicVertex(
                    model_name=self.model_name,
                    max_retries=self.max_retries,
                    ## causes issues with the pydantic model with default None value:
                    # max_output_tokens=self.max_output_tokens,
                    ## for now, claude is only available in us-east5 and europe-west1
                    # location = self.location,
                    location="us-east5",
                    temperature=self.temperature,
                    top_p=self.top_p,
                    top_k=self.top_k,
                    verbose=self.verbose
                )
            else:
                return ChatVertexAI(
                    model_name=self.model_name,
                    location=self.location,
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
    async def astream(
        self,
        input: Dict[str, Any],
    ) -> AsyncGenerator[Dict, Any]:
        """
        Abstract method to asynchronously stream the Agent output.
        This should be implemented by subclasses to handle the specific
        streaming logic of their agent executor.
        """
        pass


class GoogleAdkAgentManager(BaseAgentManager):
    """
    AgentManager subclass for Google ADK orchestration.
    """

    USER_ID = "dummy_user_id"

    def __init__(
        self,
        prompt: str,
        industry_type: str,
        location: Optional[str] = "us-central1",
        agent_engine_resource_id: Optional[str] = None,
        model_name: Optional[str] = GEMINI_FLASH_20_LATEST,
        max_retries: Optional[int] = 6,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = 0,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        return_steps: Optional[bool] = False,
        verbose: Optional[bool] = True
    ):
        # TODO: use Vertex AI Session Service for Agent Engine deployment
        self.app_name = "adk_agent_runner"
        self.session_service = InMemorySessionService()

        super().__init__(
            prompt=prompt,
            industry_type=industry_type,
            location=location,
            orchestration_framework=OrchestrationFramework.VERTEX_AI_AGENT_FRAMEWORK_AGENT.value,
            agent_engine_resource_id=agent_engine_resource_id,
            model_name=model_name,
            max_retries=max_retries,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            return_steps=return_steps,
            verbose=verbose
        )

    def create_agent_executor(self):
        """
        Creates a ADK Agent executor.
        """

        tool_names = []
        tool_desc = []
        for tool in self.tools:
            try:
                tool_names.append(tool.name)
                tool_desc.append(f"*  `{tool.name}`: {tool.description}")
            except Exception:
                continue

        tool_names = ", ".join(tool_names)
        tool_desc = "\n".join(tool_desc)

        prompt = self.prompt.format(tool_names=tool_names, tool_desc=tool_desc)

        root_agent = Agent(
            name="assistant_agent",
            model=self.model_name,
            instruction=prompt,
            tools=self.tools,
        )

        runner = Runner(
            agent=root_agent,
            app_name=self.app_name,
            session_service=self.session_service,
        )

        return runner

    async def astream(
        self,
        input: Dict[str, Any],
    ) -> AsyncGenerator[Dict, Any]:
        """Asynchronously event streams the Agent output."""
        query = input["messages"][-1]["content"]
        message = types.Content(role='user', parts=[types.Part(text=query)])

        try:
            # check if session exists, if not, create one
            session = None
            try:
                session = self.session_service.get_session(
                    app_name=self.app_name,
                    user_id=self.USER_ID,
                    session_id=input["session_id"]
                )
            finally:
                if not session:
                    self.session_service.create_session(
                        app_name=self.app_name,
                        user_id=self.USER_ID,
                        session_id=input["session_id"]
                    )

            async for event in self.agent_executor.run_async(
                    user_id=self.USER_ID,
                    session_id=input["session_id"],
                    new_message=message,
            ):
                # Events can be of various types (e.g., tool calls, intermediate steps).
                # We are interested in events that contain text content from the agent.
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_obj = {
                                "agent": {
                                    "output": part.text,
                                    "messages": [
                                        {
                                            "lc": 1,
                                            "type": "constructor",
                                            "id": ["langchain", "schema",
                                                   "messages", "AIMessage"],
                                            "kwargs": {
                                                "content": part.text,
                                                "type": "ai",
                                                "tool_calls": [],
                                                "invalid_tool_calls": [],
                                                "id": input["run_id"]
                                            }
                                        }
                                    ]
                                }
                            }
                            yield response_obj

                # Check if this event marks the completion of the agent's turn
                if event.is_final_response():
                    # [End of Agent Turn]
                    break
        except Exception as e:
            raise RuntimeError(f"Unexpected error. {e}") from e


class LangChainPrebuiltAgentManager(BaseAgentManager):
    """
    AgentManager subclass for LangChain Agent orchestration.
    """
    def __init__(
        self,
        prompt: str,
        industry_type: str,
        location: Optional[str] = "us-central1",
        agent_engine_resource_id: Optional[str] = None,
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
            location=location,
            orchestration_framework=OrchestrationFramework.LANGCHAIN_PREBUILT_AGENT.value,
            agent_engine_resource_id=agent_engine_resource_id,
            model_name=model_name,
            max_retries=max_retries,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            return_steps=return_steps,
            verbose=verbose
        )


    def create_agent_executor(self):
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


    async def astream(
        self,
        input: Dict[str, Any],
    ) -> AsyncGenerator[Dict, Any]:
        """Asynchronously event streams the Agent output.

        Args:
            input: The list of messages to send to the model as input.

        Yields:
            Dictionaries representing the streamed agent output.

        Exception:
            An error is encountered during streaming.
        """
        try:
            async for chunk in self.agent_executor.astream(
                {
                    "input": input["messages"][-1],
                    "chat_history": input["messages"][:-1],
                }
            ):
                # Organize response object to be consistent with other Agents (e.g. Agent Engine)
                if "output" in chunk:
                    response_obj = {
                        "agent": {
                            "output": chunk["output"],
                            "messages": [
                                {
                                    "lc": 1,
                                    "type": "constructor",
                                    "id": ["langchain", "schema", "messages", "AIMessage"],
                                    "kwargs": {
                                        "content": chunk["output"],
                                        "type": "ai",
                                        "tool_calls": [],
                                        "invalid_tool_calls": [],
                                        "id": input["run_id"]
                                    }
                                }
                            ]
                        }
                    }
                    yield response_obj
            return  # Exit the loop if successful
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
        location: Optional[str] = "us-central1",
        agent_engine_resource_id: Optional[str] = None,
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
            location=location,
            orchestration_framework=OrchestrationFramework.LANGGRAPH_PREBUILT_AGENT.value,
            agent_engine_resource_id=agent_engine_resource_id,
            model_name=model_name,
            max_retries=max_retries,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            return_steps=return_steps,
            verbose=verbose
        )


    def create_agent_executor(self):
        """
        Creates a LangGraph React Agent executor.
        """
        return langgraph_create_react_agent(
            prompt=self.prompt,
            model=self.model_obj,
            tools=self.tools,
            debug=self.verbose
        )


    async def astream(
        self,
        input: Dict[str, Any],
    ) -> AsyncGenerator[Dict, Any]:
        """Asynchronously event streams the Agent output.

        Args:
            input: The list of messages to send to the model as input.

        Yields:
            Dictionaries representing the streamed agent output.

        Exception:
            An error is encountered during streaming.
        """
        try:
            async for chunk in self.agent_executor.astream(input, stream_mode="values"):
                message = chunk["messages"][-1]
                if isinstance(message, AIMessage):
                    # Organize response object to be consistent with other Agents (e.g. Agent Engine)
                    response_obj = {
                        "agent": {
                            "messages": [
                                {
                                    "lc": 1,
                                    "type": "constructor",
                                    "id": ["langgraph", "schema", "messages", "AIMessage"],
                                    "kwargs": {
                                        "content": message.content,
                                        "type": "ai",
                                        "tool_calls": [],
                                        "invalid_tool_calls": [],
                                        "id": input["run_id"]
                                    },
                                    "usage_metadata": message.usage_metadata
                                }
                            ]
                        }
                    }
                    yield response_obj
            return  # Exit the loop if successful
        except Exception as e:
            raise RuntimeError(f"Unexpected error. {e}") from e


class LangChainVertexAIAgentEngineAgentManager(BaseAgentManager):
    """
    AgentManager subclass for Vertex AI Agent Engine LangChain orchestration.
    """
    def __init__(
        self,
        prompt: str,
        industry_type: str,
        location: Optional[str] = "us-central1",
        agent_engine_resource_id: Optional[str] = None,
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
            location=location,
            orchestration_framework=OrchestrationFramework.LANGCHAIN_VERTEX_AI_AGENT_ENGINE_AGENT.value,
            agent_engine_resource_id=agent_engine_resource_id,
            model_name=model_name,
            max_retries=max_retries,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            return_steps=return_steps,
            verbose=verbose
        )


    def create_agent_executor(self):
        """
        Creates a Vertex AI Agent Engine Langchain Agent executor.
        """
        # If agent_engine_resource_id is provided, use the deployed Agent Engine
        if self.agent_engine_resource_id:
            langchain_agent = reasoning_engines.ReasoningEngine(self.agent_engine_resource_id)
        else:
            langchain_agent = reasoning_engines.LangchainAgent(
                # prompt=self.prompt, # Custom prompt seems to have an issue for some reason
                model=self.model_name,
                tools=self.tools,
                agent_executor_kwargs={
                    "return_intermediate_steps": self.return_steps,
                    "verbose": self.verbose
                },
                enable_tracing=True
            )
            langchain_agent.set_up()
        return langchain_agent


    async def astream(
        self,
        input: Dict[str, Any],
    ) -> AsyncGenerator[Dict, Any]:
        """
        Asynchronously streams the Agent output using Vertex AI Agent engine.

        Args:
            input: The list of messages to send to the model as input.

        Yields:
            Dictionaries representing the streamed agent output.

        Exception:
            An error is encountered during streaming.
        """
        # Convert the messages into a string
        content = "\n".join(f"[{msg['type']}]: {msg['content']}" for msg in input["messages"])
        try:
            for chunk in self.agent_executor.stream_query(input=content):
                chunk["messages"] = [{**msg, "kwargs": {**msg["kwargs"], "id": input["run_id"]}} for msg in chunk["messages"]]
                yield {"agent": chunk}
        except Exception as e:
            raise RuntimeError(f"Unexpected error. {e}") from e


class LangGraphVertexAIAgentEngineAgentManager(BaseAgentManager):
    """
    AgentManager subclass for Vertex AI Agent Engine LangGraph orchestration.
    """
    def __init__(
        self,
        prompt: str,
        industry_type: str,
        location: Optional[str] = "us-central1",
        agent_engine_resource_id: Optional[str] = None,
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
            location=location,
            orchestration_framework=OrchestrationFramework.LANGGRAPH_VERTEX_AI_AGENT_ENGINE_AGENT.value,
            agent_engine_resource_id=agent_engine_resource_id,
            model_name=model_name,
            max_retries=max_retries,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            return_steps=return_steps,
            verbose=verbose
        )


    def create_agent_executor(self):
        """
        Creates a Vertex AI Agent Engine LangGraph Agent executor.
        """
        # If agent_engine_resource_id is provided, use the deployed Agent Engine
        if self.agent_engine_resource_id:
            langgraph_agent = reasoning_engines.ReasoningEngine(self.agent_engine_resource_id)
        else:
            langgraph_agent = reasoning_engines.LanggraphAgent(
                model=self.model_name,
                tools=self.tools,
                runnable_kwargs={"prompt": self.prompt, "debug": self.verbose},
                enable_tracing=True
            )
            langgraph_agent.set_up()
        return langgraph_agent


    async def astream(
        self,
        input: Dict[str, Any],
    ) -> AsyncGenerator[Dict, Any]:
        """
        Asynchronously streams the Agent output using Vertex AI Agent Engine.

        Args:
            input: The list of messages to send to the model as input.

        Yields:
            Dictionaries representing the streamed agent output.

        Exception:
            An error is encountered during streaming.
        """
        try:
            for chunk in self.agent_executor.stream_query(
                input=input,
                stream_mode="values"
            ):
                # Override the each of the run_ids with the one from the server
                chunk["messages"] = [{**msg, "kwargs": {**msg["kwargs"], "id": input["run_id"]}} for msg in chunk["messages"]]

                if self.agent_engine_resource_id:
                    if chunk["messages"][-1]["id"][-1] == "AIMessage":
                        yield {"agent": chunk}
                else:
                    yield {"agent": chunk}
        except Exception as e:
            raise RuntimeError(f"Unexpected error. {e}") from e


class LlamaIndexAgentManager(BaseAgentManager):
    """
    AgentManager subclass for LangGraph Agent orchestration.
    """
    def __init__(
        self,
        prompt: str,
        industry_type: str,
        location: Optional[str] = "us-central1",
        agent_engine_resource_id: Optional[str] = None,
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
            location=location,
            orchestration_framework=OrchestrationFramework.LLAMAINDEX_AGENT.value,
            agent_engine_resource_id=agent_engine_resource_id,
            model_name=model_name,
            max_retries=max_retries,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            return_steps=return_steps,
            verbose=verbose
        )
        self.model_obj = LangChainLLM(self.model_obj)


    def get_tools(self):
        """
        Helper method to retrieve tools based on the industry type.

        Returns:
            A list of tools for the agent to use, based on the industry type.
        """
        return get_llamaindex_tools(self.industry_type)


    def create_agent_executor(self):
        """
        Creates a LlamaIndex React Agent executor.
        """
        # setup the index/query llm for Vertex Search
        Settings.llm = LangChainLLM(self.model_obj)
        llamaindex_agent = ReActAgent.from_tools(
            prompt=self.prompt,
            llm = LangChainLLM(self.model_obj),
            tools=self.tools,
            verbose=self.verbose
        )
        return llamaindex_agent


    def get_response_obj(
        self,
        content: str,
        run_id: str
    ) -> Dict:
        """Returns a structure dictionary response object.
        The response object needs to be organized to be
        consistent with other Agents (e.g. Agent Engine)

        Args:
            content: The string reponse from the LLM.
            run_id: The run_id.

        Returns:
            Structured dictionary reponse object.
        """
        response_obj = {
            "agent": {
                "messages": [
                    {
                        "lc": 1,
                        "type": "constructor",
                        "id": ["llamaindex", "schema", "messages", "AIMessage"],
                        "kwargs": {
                            "content": content,
                            "type": "ai",
                            "tool_calls": [],
                            "invalid_tool_calls": [],
                            "id": run_id
                        },
                    }
                ]
            }
        }
        return response_obj


    async def astream(
        self,
        input: Dict[str, Any],
    ) -> AsyncGenerator[Dict, Any]:
        """Asynchronously event streams the Agent output. Needs to be
        an Iterable for Agent Engine deployments

        Args:
            input: The list of messages to send to the model as input.

        Yields:
            Dictionaries representing the streamed agent output.

        Exception:
            An error is encountered during streaming.
        """
        try:
            if self.agent_engine_resource_id:
                llamaindex_agent = reasoning_engines.ReasoningEngine(self.agent_engine_resource_id)
                # Uses the stream_query function below
                response = llamaindex_agent.stream_query(input=input)
                for chunk in response:
                    yield chunk
            else:
                # Convert the messages into a string
                content = "\n".join(f"[{msg['type']}]: {msg['content']}" for msg in input["messages"])
                response = await self.agent_executor.aquery(content)
                yield self.get_response_obj(
                    content=response.response,
                    run_id=input["run_id"]
                )

        except Exception as e:
            raise RuntimeError(f"Unexpected error. {e}") from e

    # # alias stream_query for Agent Engine deployments
    # stream_query = astream

    def stream_query(
        self,
        input: Dict[str, Any]
    ) -> Generator:
        """Synchronously event streams the Agent output.
        This function is an alias for astream for Agent Engine deployments

        Args:
            input: The list of messages to send to the model as input.

        Yields:
            Dictionaries representing the streamed agent output.

        Exception:
            An error is encountered during processing.
        """
        run_id = uuid.uuid4()

        # If using Agent Engine, explicitly re-set the index/query llm for Vertex Search
        Settings.llm = self.model_obj

        try:
            # Convert the messages into a string
            content = "\n".join(f"[{msg['type']}]: {msg['content']}" for msg in input["messages"])
            response = self.agent_executor.query(content)
            yield self.get_response_obj(
                content=response.response,
                run_id=run_id
            )

        except Exception as e:
            raise RuntimeError(f"Unexpected error. {e}") from e
