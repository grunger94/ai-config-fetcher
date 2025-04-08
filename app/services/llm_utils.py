import logging
import os

from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.models.schemas import AppEnvExtractionOutput

APP_LIST = os.getenv("APP_LIST", "").split(",")
ENV_LIST = os.getenv("ENV_LIST", "").split(",")

logger = logging.getLogger(__name__)

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", max_retries=2)
app_env_parser = PydanticOutputParser(pydantic_object=AppEnvExtractionOutput)

def extract_apps_and_envs(query: str) -> AppEnvExtractionOutput:
    prompt = PromptTemplate.from_template("""
        Your job is to extract applications and environments mentioned in user questions based off a universe of known data:

        Known apps: "{app_list}"
        Known environments: "{env_list}"

        If the query doesn't mention any specific applications, return the entire list of known apps.
        If the query doesn't mention any specific environments, return the entire list of  environments.
        
        Respond only with a JSON object in this format:
        {{
          "apps": [...],
          "envs": [...]
        }}
        Query:
        
        {query}
        """)

    app_env_chain = (prompt | llm | app_env_parser)

    return app_env_chain.invoke({
        "query": query,
        "app_list": ", ".join(APP_LIST),
        "env_list": ", ".join(ENV_LIST)
    })

def filter_relevant_config(query, config_json):
    prompt = PromptTemplate.from_template("""
        Your job is to analyze the content of a configuration JSON and determine if its data could be useful to answer the question below.

        App: {app_name}
        Env: {env_name}
        Configuration file content:
        ---
        {config_json}
        ---
        
        User question: {query}

        Does this data help answer the question? 
        - If yes, return the relevant parts of the configuration following the JSON format below:
            {{"app_name": app, "env_name": env, "config": <insert relevant information here>}}
        - If not, just return None.
        
        Important:
        - Only respond with a raw JSON object (as string).
        - Do NOT wrap the response in code blocks or markdown.
        """)

    return (prompt | llm).invoke({
        "query": query,
        "app_name": config_json["app_name"],
        "env_name": config_json["env_name"],
        "config_json": config_json["content"]
    })

def answer_user_question(query, relevant_configs):
    relevant_configs_str = "\n".join(relevant_configs)

    prompt = PromptTemplate.from_template("""
            Use the following JSON objects to answer user question below:
            ---
            {config_str}
            ---
            
            Question: {query}
            
            When there is a concise answer, for example, a single application name or a list of environment names, don't explain your reasoning.
            
            """)

    formatted_prompt = prompt.format(config_str=relevant_configs_str, query=query)
    logger.debug(f"Final prompt sent to LLM:\n{formatted_prompt}")

    llm_output = llm.invoke(formatted_prompt)
    return llm_output.content