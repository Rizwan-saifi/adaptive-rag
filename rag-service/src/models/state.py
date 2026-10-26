"""
State model for the graph-based RAG system.
"""

from typing import TypedDict, Annotated, Optional

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


class State(TypedDict):
    """State schema for the RAG graph."""

    messages: Annotated[list[AnyMessage], add_messages]
    binary_score: Optional[str]
    route: Optional[str]
    # The user's question as asked; latest_query may be a rewrite of it
    question: Optional[str]
    latest_query: Optional[str]
    user_id: str
    rewrite_count: Optional[int]