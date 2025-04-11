import logging

from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import JSONAgentOutputParser
from langchain.tools.render import render_text_description_and_args
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", max_retries=2)


def invoke_llm(prompt, args, parser):
    if parser:
        runnable = (prompt | llm | parser)
    else:
        runnable = (prompt | llm)

    return runnable.invoke(args)

def build_prompt_with_tools(chat_prompt, tools):
    return chat_prompt.partial(
        tools=render_text_description_and_args(list(tools)),
        tool_names=", ".join([t.name for t in tools]),
    )

def build_chain(prompt):
    return (
            RunnablePassthrough.assign(
                agent_scratchpad=lambda x: format_log_to_str(x["intermediate_steps"]),
            )
            | prompt
            | llm
            | JSONAgentOutputParser()
    )