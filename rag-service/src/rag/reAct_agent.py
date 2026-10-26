"""
Tool-calling agent setup for document retrieval and question answering.
"""

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.agents.agent import RunnableMultiActionAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.config.settings import Config
from src.llms.provider import llm
from src.rag.retriever_setup import get_retriever

config = Config()

# Native tool calling works across Groq, OpenAI, Gemini and Anthropic. (A text
# "Thought:/Action:" ReAct prompt is refused by current Claude models.)
prompt = ChatPromptTemplate.from_messages([
    ("system", config.prompt("system_prompt")),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])


def get_agent_executor() -> AgentExecutor:
    """
    Build the agent with a retriever over the current vector store.

    Built per request so documents uploaded after startup are searchable.
    """
    tools = [get_retriever()]
    agent = RunnableMultiActionAgent(
        runnable=create_tool_calling_agent(llm, tools, prompt),
        # invoke rather than stream, so provider wrappers see whole responses
        stream_runnable=False,
    )
    return AgentExecutor(
        agent=agent,
        tools=tools,
        handle_parsing_errors=True,
        max_iterations=3,
        verbose=True,
        return_intermediate_steps=True,
    )
