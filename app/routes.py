import logging

from flask import request, jsonify

from app.services.llm_utils import invoke_agent_executor, answer_user_question

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def configure_routes(app):
    @app.route("/query", methods=["POST"])
    def query_system():
        data = request.json
        query = data.get("query")

        response = invoke_agent_executor({"query": query})

        configs =  response["output"]
        logger.debug(f"Fetched configurations: {configs}")

        final_answer = answer_user_question(query, configs)
        logger.info(f"Final answer: {final_answer.content}")

        return jsonify({"response": final_answer.content})
