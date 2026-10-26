"""
Query request model.
"""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for RAG queries."""

    query: str = Field(min_length=1, max_length=10_000)
    # Which of the user's conversations the query belongs to; chosen by the client
    conversation_id: str = Field(min_length=1, max_length=100)
