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
# pylint: disable=C0301
"""Module that contains various utility functions."""
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from app.orchestration.agent import (
    LangChainPrebuiltAgentManager,
    LangGraphPrebuiltAgentManager,
    LangChainVertexAIAgentEngineAgentManager,
    LangGraphVertexAIAgentEngineAgentManager,
    LlamaIndexAgentManager,
    GoogleAdkAgentManager
)
from app.orchestration.constants import (
    FINANCE_AGENT_DESCRIPTION,
    HEALTHCARE_AGENT_DESCRIPTION,
    RETAIL_AGENT_DESCRIPTION,
    DEFAULT_AGENT_DESCRIPTION
)
from app.orchestration.enums import (
    IndustryType,
    OrchestrationFramework
)


def get_init_prompt(
        agent_orchestration_framework: str,
        industry_type: str
) -> ChatPromptTemplate:
    """Creates the initialization prompt for the agent based on the industry."""

    if industry_type == IndustryType.FINANCE_INDUSTRY.value:
        sys_desc = FINANCE_AGENT_DESCRIPTION
    elif industry_type == IndustryType.HEALTHCARE_INDUSTRY.value:
        sys_desc = HEALTHCARE_AGENT_DESCRIPTION
    elif industry_type == IndustryType.RETAIL_INDUSTRY.value:
        sys_desc = RETAIL_AGENT_DESCRIPTION
    else:
        sys_desc = DEFAULT_AGENT_DESCRIPTION

    # The prebuilt langchain option is older and has a different prompt structure
    if agent_orchestration_framework == OrchestrationFramework.LANGCHAIN_PREBUILT_AGENT.value:
        return PromptTemplate.from_template(sys_desc + """You have access to the following tools:
                         
        TOOLS:
        ------

        Assistant has access to the following tools:

        {tools}

        To use a tool, please use the following format:

        ```
        Thought: Do I need to use a tool? Yes
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ```

        When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

        ```
        Thought: Do I need to use a tool? No
        Final Answer: [your response here]
        ```

        Begin!

        Previous conversation history:
        {chat_history}

        New input: {input}
        {agent_scratchpad}""")

    elif agent_orchestration_framework ==OrchestrationFramework.LLAMAINDEX_AGENT.value:
        return sys_desc + """You are designed to help with a variety of tasks, from answering questions to providing summaries to other types of analyses.
        When you respond, do not respond with backticks (e.g. ```). Remove these from your response.

        ## Tools

        You have access to a wide variety of tools. You are responsible for using the tools in any sequence you deem appropriate to complete the task at hand.
        This may require breaking the task into subtasks and using different tools to complete each subtask.

        You have access to the following tools:
        {tool_desc}


        ## Output Format

        Please answer in the same language as the question and use the following format:

        ```
        Thought: The current language of the user is: (user\'s language). I need to use a tool to help me answer the question.
        Action: tool name (one of {tool_names}) if using a tool.
        Action Input: the input to the tool, in a JSON format representing the kwargs (e.g. {{"input": "hello world", "num_beams": 5}})
        ```

        Please ALWAYS start with a Thought.

        NEVER surround your response with markdown code markers. You may use code markers within your response if you need to.

        Please use a valid JSON format for the Action Input. Do NOT do this {{\'input\': \'hello world\', \'num_beams\': 5}}.

        If this format is used, the tool will respond in the following format:

        ```
        Observation: tool response
        ```

        You should keep repeating the above format till you have enough information to answer the question without using any more tools. At that point, you MUST respond in one of the following two formats:

        ```
        Thought: I can answer without using any more tools. I\'ll use the user\'s language to answer
        Answer: [your answer here (In the same language as the user\'s question)]
        ```

        ```
        Thought: I cannot answer the question with the provided tools.
        Answer: [your answer here (In the same language as the user\'s question)]
        ```

        ## Current Conversation

        Below is the current conversation consisting of interleaving human and assistant messages.
        """

    elif agent_orchestration_framework == OrchestrationFramework.VERTEX_AI_AGENT_FRAMEWORK_AGENT.value:
        return sys_desc + """You are designed to help with a variety of tasks, from answering questions to providing summaries to other types of analyses.
        When you respond, do not respond with backticks (e.g. ```). Remove these from your response.

        ## Tools

        You have access to a wide variety of tools. You are responsible for using the tools in any sequence you deem appropriate to complete the task at hand.
        This may require breaking the task into subtasks and using different tools to complete each subtask.

        You have access to the following tools:
        {tool_desc}


        ## Output Format

        Please answer in the same language as the question and use the following format.

        NEVER surround your response with markdown code markers. You may use code markers within your response if you need to.

        Please use a valid JSON format for the Action Input. Do NOT do this {{\'input\': \'hello world\', \'num_beams\': 5}}.
        """

    else:
        return ChatPromptTemplate.from_messages([
            ("system", f"{sys_desc}"),
            ("placeholder", "{messages}")
        ])

def get_agent_from_config(
        agent_orchestration_framework: str,
        agent_foundation_model: str,
        industry_type: str,
        agent_engine_resource_id: str = None,
    ):
    """Returns the associated Agent Manager based on the defined selection"""

    # Set up the agent backed on environment variables for user config
    init_prompt = get_init_prompt(agent_orchestration_framework, industry_type)

    # Set up agent type based on user config selection
    if agent_orchestration_framework == OrchestrationFramework.LANGCHAIN_PREBUILT_AGENT.value:
        agent_manager = LangChainPrebuiltAgentManager(
            prompt=init_prompt,
            industry_type=industry_type,
            model_name=agent_foundation_model,
            agent_engine_resource_id=agent_engine_resource_id
        )
    elif agent_orchestration_framework == OrchestrationFramework.LANGCHAIN_VERTEX_AI_AGENT_ENGINE_AGENT.value:
        agent_manager = LangChainVertexAIAgentEngineAgentManager(
            prompt=init_prompt,
            industry_type=industry_type,
            model_name=agent_foundation_model,
            agent_engine_resource_id=agent_engine_resource_id
        )
    elif agent_orchestration_framework == OrchestrationFramework.LANGGRAPH_PREBUILT_AGENT.value:
        agent_manager = LangGraphPrebuiltAgentManager(
            prompt=init_prompt,
            industry_type=industry_type,
            model_name=agent_foundation_model,
            agent_engine_resource_id=agent_engine_resource_id
        )
    elif agent_orchestration_framework == OrchestrationFramework.LANGGRAPH_VERTEX_AI_AGENT_ENGINE_AGENT.value:
        agent_manager = LangGraphVertexAIAgentEngineAgentManager(
            prompt=init_prompt,
            industry_type=industry_type,
            model_name=agent_foundation_model,
            agent_engine_resource_id=agent_engine_resource_id
        )
    elif agent_orchestration_framework == OrchestrationFramework.LLAMAINDEX_AGENT.value:
        agent_manager = LlamaIndexAgentManager(
            prompt=init_prompt,
            industry_type=industry_type,
            model_name=agent_foundation_model,
            agent_engine_resource_id=agent_engine_resource_id
        )
    elif agent_orchestration_framework == OrchestrationFramework.VERTEX_AI_AGENT_FRAMEWORK_AGENT.value:
        agent_manager = GoogleAdkAgentManager(
            prompt=init_prompt,
            industry_type=industry_type,
            model_name=agent_foundation_model,
            agent_engine_resource_id=agent_engine_resource_id
        )
    else:
        # default agent orchestration is LangGraphPrebuiltAgentManager
        agent_manager = LangGraphPrebuiltAgentManager(
            prompt=init_prompt,
            industry_type=industry_type,
            model_name=agent_foundation_model,
            agent_engine_resource_id=agent_engine_resource_id
        )

    return agent_manager
