import logging

import streamlit as st
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

from app.services.llm_utils import answer_user_question, create_agent_executor

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def print_messages():
    for msg in st.session_state.langchain_history.messages:
        if msg.type == "human":
            st.chat_message("user").write(msg.content)
        elif msg.type == "ai":
            st.chat_message("assistant").write(msg.content)

st.title("Configuration Search Assistant")

if "memory" not in st.session_state:
    st.session_state.langchain_history = StreamlitChatMessageHistory()
    st.session_state.memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        chat_memory=st.session_state.langchain_history
    )

print_messages()

user_input = st.chat_input("Ask me about any config...")

if user_input:
    agent_executor = create_agent_executor(st.session_state.memory)
    agent_response = agent_executor.invoke({"input": user_input})
    relevant_configs = agent_response["output"]
    response = answer_user_question(user_input, relevant_configs)
    st.session_state.langchain_history.add_ai_message(response.content)

    print_messages()
