import json
import logging
import os

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.mock.json_mock import get_json_mock
from app.services.llm_core import invoke_llm
from app.services.vector_storage import store_embedding, get_stored_hash, fetch_configurations
from app.utils.hashing import get_file_hash

logger = logging.getLogger(__name__)

APP_LIST = os.getenv("APP_LIST", "").split(",")
ENV_LIST = os.getenv("ENV_LIST", "").split(",")

def extract_apps_and_envs(query: str):
    """
    Parses the user query to extract relevant application and environment names.
    Returns a dictionary with 'app_list' and 'env_list' as keys.
    """

    prompt = PromptTemplate.from_template("""
        Your job is to extract applications and environments mentioned in user questions based off a universe of known data:

        Known apps: "{known_apps}"
        Known environments: "{known_envs}"

        If the query doesn't mention any specific applications, return the entire list of known apps.
        If the query doesn't mention any specific environments, return the entire list of known environments.
        
        Respond only with a raw JSON object in this format:
        {{
          "app_list": [...],
          "env_list": [...]
        }}
        Query:
        
        {query}
        """)

    return invoke_llm(prompt, {
        "query": query,
        "known_apps": ", ".join(APP_LIST),
        "known_envs": ", ".join(ENV_LIST)
    }, JsonOutputParser())

def extract_keys(query: str):
    """
    Take a natural language query and returns only the config keys that seem relevant to answering it.
    """

    prompt = PromptTemplate.from_template("""
        Your job is to extract only the relevant configuration keys that are mentioned or implied in the query. 
        These are specific key names like "log_level", "enable_feature_x", "timeout", etc.
    
        Given this user query:
        "{query}"
    
        Return a JSON list of strings. Example:
        ["log_level", "enable_feature_x"]
        
        If no keys are identified, return an empty JSON list.
        """)

    return invoke_llm(prompt, {"query": query}, JsonOutputParser())

def update_database_configurations(apps, envs):
    """
    Fetches configuration data for each app-env combination individually and stores their embeddings into a vectorstore.
    """

    for app_name in apps:
        for env_name in envs:
            __fetch_and_embed_app_env_config(app_name, env_name)

def fetch_configs_by_scope(apps, envs, relevant_keys=None):
    """
    Retrieve configuration data from PostgreSQL for the given applications and environments.
    Optionally filters each config to only include a set of relevant keys.

    Args:
        apps (List[str]): List of application names.
        envs (List[str]): List of environment names.
        relevant_keys (List[str], optional): List of keys to retain from the configuration.
                                             If None, returns full config content.

    Returns:
        List[Dict]: A list of dicts containing app_name, env_name, and filtered content.
    """

    result = []

    for app_name, env_name, content_json in fetch_configurations(apps, envs):
        content_dict = json.loads(content_json)

        if relevant_keys:
            filtered_content = {}
            for key in relevant_keys:
                keys = key.split('.')  # Split key into parts if it's a nested key
                value = __get_nested_value(content_dict, keys)
                if value is not None:
                    # Rebuild the filtered content using nested keys
                    nested_dict = filtered_content
                    for sub_key in keys[:-1]:
                        nested_dict = nested_dict.setdefault(sub_key, {})
                    nested_dict[keys[-1]] = value
        else:
            filtered_content = content_dict

        result.append({
            "app_name": app_name,
            "env_name": env_name,
            "content": filtered_content
        })

    return result

def __fetch_and_embed_app_env_config(application_name, environment_name):
    """
    Fetch, check, and persist the configuration in PostgreSQL vectorstore.
    """

    json_content = get_json_mock(application_name, environment_name)  # Mocking API response
    new_hash = get_file_hash(json.dumps(json_content))
    file_name = f"{application_name}-{environment_name}"

    stored_hash = get_stored_hash(application_name, environment_name)

    if stored_hash == new_hash:
        logger.debug(f"No changes detected for {file_name}, skipping ingestion")
    else:
        # Store new embedding
        store_embedding(application_name, environment_name, json.dumps(json_content), new_hash)

def __get_nested_value(d, keys):
    """
    Retrieve the value from a dictionary for a list of nested keys.
    """

    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return None
    return d