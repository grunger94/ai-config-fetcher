import json
import logging

from flask import request, jsonify

from app.services.config_fetcher import fetch_and_embed_all_configs
from app.services.llm_utils import extract_apps_and_envs, filter_relevant_config, answer_user_question
from app.services.vector_search import retrieve_similar_configs

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def configure_routes(app):
    @app.route("/query", methods=["POST"])
    def query_system():
        data = request.json
        query = data.get("query")

        logger.debug(f"Received query: {query}")

        extracted_info = extract_apps_and_envs(query)

        apps, envs = extracted_info.apps, extracted_info.envs

        if len(apps) == 0 or len(envs) == 0:
            return jsonify({"response": f"I'm sorry, I don't have enough information to answer your question. Please provide the JSON configuration data. Found apps/envs: {extracted_info}"})

        logger.debug(f"Extracted info from query: apps={apps} envs={envs}")

        config_data = fetch_and_embed_all_configs(apps, envs)
        logger.debug(f"Fetched config data={config_data}")

        top_k = len(apps) * len(envs) * 2
        similar_configs = retrieve_similar_configs(query, top_k)

        relevant_configs = []

        for config in similar_configs:
            app_name = config["app_name"]
            env_name = config["env_name"]

            evaluated_config = filter_relevant_config(query, config)

            config_content = evaluated_config.content

            if not config_content.lower().startswith("none"):
                relevant_config = config_content
                logger.debug(f"Appending relevant config for the LLM to respond to user query: {relevant_config}")
                relevant_configs.append(relevant_config)
            else:
                logger.debug(f"{app_name}-{env_name} considered irrelevant by the LLM")

        response = answer_user_question(query, relevant_configs)
        logger.info(f"Final LLM response: {response}")

        return jsonify({"response": response})
