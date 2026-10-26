"""
Graph builder module for the adaptive RAG system.

    condense_question -> retrieve -> classify -+-> generate                      (documents answer it)
                                               +-> general_llm                   (general knowledge)
                                               +-> web_search -> generate        (needs fresh/external info)

The classifier sees the retrieved chunks, so it also decides whether they are
relevant enough to answer from.
"""

import logging
from typing import Literal

from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_tavily import TavilySearch
from langgraph.constants import START, END
from langgraph.graph.state import StateGraph

from src.config.settings import Config
from src.core.config import settings
from src.llms.provider import get_llm, message_text, structured_llm
from src.models.route_identifier import RouteIdentifier
from src.models.state import State
from src.rag.retriever_setup import search

logger = logging.getLogger(__name__)
config = Config()

condense_prompt = PromptTemplate.from_template(config.prompt("condense_prompt"))
classify_prompt = PromptTemplate.from_template(config.prompt("classify_prompt"))
generate_prompt = PromptTemplate.from_template(config.prompt("generate_prompt"))

# Nodes whose model output is the answer shown to the user (used for streaming)
ANSWER_NODES = {"generate", "general_llm"}


def format_documents(documents: list[Document]) -> str:
    """Join chunks into one context string, labelling each with its source."""
    parts = []
    for doc in documents:
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page_label")
        label = f"{source}, page {page}" if page else source
        parts.append(f"[source: {label}]\n{doc.page_content}")
    return "\n\n".join(parts)


# Node implementations
def condense_question(state: State):
    """
    Rewrite a follow-up question so it can be understood without the conversation.

    Args:
        state (State): The current state of the graph.

    Returns:
        dict: The standalone question.
    """
    *history, latest = state["messages"]
    question = message_text(latest.content)
    if history:
        transcript = "\n".join(f"{m.type}: {message_text(m.content)}" for m in history)
        result = (condense_prompt | get_llm()).invoke({"history": transcript, "question": question})
        question = message_text(result.content).strip() or question
        logger.info("Standalone question: %s", question)
    return {"question": question}


def retrieve(state: State):
    """
    Fetch the user's document chunks relevant to the question.

    Args:
        state (State): The current state of the graph.

    Returns:
        dict: The retrieved chunks.
    """
    documents = search(state["user_id"], state["question"])
    logger.info("Retrieved %d chunks", len(documents))
    return {"documents": documents}


def classify(state: State):
    """
    Decide whether the retrieved chunks answer the question, or where else to look.

    Args:
        state (State): The current state of the graph.

    Returns:
        dict: The route, and the chunks as context if they answer the question.
    """
    documents = state["documents"]
    context = format_documents(documents) if documents else "No documents found."
    result = (classify_prompt | structured_llm(RouteIdentifier)).invoke(
        {"question": state["question"], "context": context}
    )
    route = result.route
    if route == "index" and not documents:
        route = "general"
    logger.info("Route: %s", route)
    return {"route": route, "context": context if route == "index" else None}


def general_llm(state: State):
    """
    Answer from the model's general knowledge, with the conversation as context.

    Args:
        state (State): The current state of the graph.

    Returns:
        dict: The answer message.
    """
    result = get_llm().invoke(state["messages"])
    return {"messages": [AIMessage(content=message_text(result.content))]}


def web_search(state: State):
    """
    Search the web for the question.

    Args:
        state (State): The current state of the graph.

    Returns:
        dict: The search results as context, or no context if the search failed.
    """
    try:
        response = TavilySearch(max_results=5).invoke({"query": state["question"]})
    except Exception:
        logger.exception("Web search failed")
        return {"context": None}
    if "error" in response:
        logger.warning("Web search failed: %s", response["error"])
        return {"context": None}

    context = "\n\n".join(
        f"[source: {item.get('url', 'web')}]\n{item['content']}"
        for item in response.get("results", [])
        if item.get("content")
    )
    return {"context": context or None}


def generate(state: State):
    """
    Generate the final answer from the context.

    Args:
        state (State): The current state of the graph.

    Returns:
        dict: The answer message.
    """
    result = (generate_prompt | get_llm()).invoke(
        {"question": state["question"], "context": state["context"]}
    )
    return {"messages": [AIMessage(content=message_text(result.content))]}


# Routing
def route_after_classify(state: State) -> Literal["generate", "general_llm", "web_search"]:
    """Follow the classifier's route; without a Tavily key, answer from general knowledge."""
    if state["route"] == "index":
        return "generate"
    if state["route"] == "search" and settings.TAVILY_API_KEY:
        return "web_search"
    return "general_llm"


def route_after_search(state: State) -> Literal["generate", "general_llm"]:
    """Answer from the search results, or from general knowledge if the search found nothing."""
    return "generate" if state.get("context") else "general_llm"


# Build the graph
graph = StateGraph(State)

graph.add_node("condense_question", condense_question)
graph.add_node("retrieve", retrieve)
graph.add_node("classify", classify)
graph.add_node("generate", generate)
graph.add_node("general_llm", general_llm)
graph.add_node("web_search", web_search)

graph.add_edge(START, "condense_question")
graph.add_edge("condense_question", "retrieve")
graph.add_edge("retrieve", "classify")
graph.add_conditional_edges("classify", route_after_classify)
graph.add_conditional_edges("web_search", route_after_search)
graph.add_edge("generate", END)
graph.add_edge("general_llm", END)

rag_graph = graph.compile()
