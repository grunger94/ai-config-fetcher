import json
import logging

from langchain.agents import Tool, AgentExecutor
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.tools import StructuredTool

from app.services.llm_core import build_chain, build_prompt_with_tools, invoke_llm
from app.services.tools import extract_apps_and_envs, extract_keys, update_database_configurations, \
    fetch_configs_by_scope

logger = logging.getLogger(__name__)

def create_agent_executor(memory):
    chat_prompt = __get_chat_prompt()
    tools = __get_llm_tools()
    prompt = build_prompt_with_tools(chat_prompt, tools)
    chain = build_chain(prompt)

    return AgentExecutor(
        agent=chain,
        tools=tools,
        memory=memory,
        handle_parsing_errors=True,
        verbose=True
    )

def answer_user_question(query: str, relevant_configs: list[dict]):
    relevant_configs_str = json.dumps(relevant_configs)

    prompt = PromptTemplate.from_template("""
            Use the following JSON objects to respond to the user query below:
            ---
            {config_str}
            ---

            Query: {input}

            When there is a concise answer, for example, a single application name or a list of environment names, don't explain your reasoning.
            If the user is only giving you an application and environment (or a list), assume they are asking you to retrieve entire config files.
            """)

    # formatted_prompt = prompt.format(
    #     input= query,
    #     config_str= relevant_configs_str
    # )

    # logger.debug(f"Final answer chain prompt: {formatted_prompt}")

    return invoke_llm(prompt, {
        "input": query,
        "config_str": relevant_configs_str
    }, None)


def __get_chat_prompt():
    return ChatPromptTemplate.from_messages(
        [
            ("system", __get_system_prompt()),
            ("human", __get_human_prompt()),
        ]
    )

def __get_system_prompt():
    system_prompt = """
            Respond to the human as helpfully and accurately as possible.

            You have access to the following tools: {tools}.
            You also have access to the following conversation history, which you can use to get relevant information 
            from previous interactions, specially for **follow-up questions**:
            ---
            {chat_history}
            ---
        
            **Always** prioritize use of chat history over tools.
             
            Only call tools if:
            - You need new information that is NOT already available in the chat history.
            - You cannot answer the question with what the user and you have already discussed.
            
            If you need to call tools, do it in the strict order outlined below:
            
            1. "extract_apps_and_envs"
            2. "extract_keys"
            3. "update_database_configurations"
            4. "fetch_configs_by_scope"

            Your task is NOT to answer the human's question directly at this point.
            Instead, your goal is to gather the necessary and relevant configuration data needed to answer the question.
            Think of your role as an information gatherer. 

            Use a JSON BLOB to specify a tool by providing an action key (tool name) and an action_input key (tool input).
            Valid "action" values: "Final Answer" or {tool_names}.
            Provide only ONE action per JSON BLOB.

            Observation: action result
            ... (repeat Thought/Action/Observation N times)
            Thought: I know what to do next to gather the information
            Action:
            {{"action": "{{next_tool_name}}", "action_input": {{input_for_tool}}}}

            When you've gathered the required information, output the action with "Final Answer" as the action, including 
            the **exact, unaltered** data from the fetch_configs_by_scope tool.

            Important:
            Only respond with a raw JSON object. Do NOT wrap the response in code blocks or markdown.

            Begin!
            """

    return system_prompt

def __get_human_prompt():
    human_prompt = """
            {input}
            {agent_scratchpad}
            """
    return human_prompt

def __get_llm_tools():
    tools = [
        Tool(
            name="extract_apps_and_envs",
            description="""
                    Parses the user query to extract relevant application and environment names.
                    Returns a dictionary with 'app_list' and 'env_list' as keys.
                    """,
            func=extract_apps_and_envs
        ),
        Tool(
            name="extract_keys",
            description="Takes a natural language query and returns only the config keys that seem relevant to answering it.",
            func=extract_keys
        ),
        StructuredTool.from_function(
            name="update_database_configurations",
            description="Fetches config data for each application and environment and updates embeddings in the database.",
            func=update_database_configurations
        ),
        StructuredTool.from_function(
            name="fetch_configs_by_scope",
            description=(
                "Fetches configuration data from the database for specific apps and environments. "
                "Only returns keys listed in relevant_keys, if provided."
            ),
            func=fetch_configs_by_scope,
        )
    ]
    return tools