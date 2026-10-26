"""
State model for the graph-based RAG system.
"""

from typing import TypedDict, Annotated, Optional

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


class State(TypedDict):
    """State schema for the RAG graph."""

    # Recent conversation, ending with the user's new question
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: str
    # The new question rewritten to stand on its own, without the conversation
    question: Optional[str]
    # The user's chunks retrieved for the question
    documents: Optional[list[Document]]
    route: Optional[str]
    # Text the final answer is generated from (document chunks or web results)
    context: Optional[str]
