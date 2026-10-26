"""
Records of users' uploaded documents, used to list and delete them.

The document chunks themselves live in the vector store.
"""

from datetime import datetime, timezone
from typing import List, Optional

from src.db.mongo_client import db

collection = db["documents"]


async def add(user_id: str, doc_id: str, filename: str, description: str, chunks: int) -> dict:
    """Record an uploaded document and return the record."""
    record = {
        "doc_id": doc_id,
        "user_id": user_id,
        "filename": filename,
        "description": description,
        "chunks": chunks,
        "uploaded_at": datetime.now(timezone.utc),
    }
    await collection.insert_one(dict(record))
    return record


async def list_for_user(user_id: str) -> List[dict]:
    """The user's documents, newest first."""
    cursor = collection.find({"user_id": user_id}, {"_id": 0}).sort("uploaded_at", -1)
    return await cursor.to_list(length=None)


async def get(user_id: str, doc_id: str) -> Optional[dict]:
    """One of the user's documents, or None if they have no such document."""
    return await collection.find_one({"user_id": user_id, "doc_id": doc_id}, {"_id": 0})


async def delete(user_id: str, doc_id: str) -> None:
    """Remove a document's record."""
    await collection.delete_one({"user_id": user_id, "doc_id": doc_id})


async def ensure_indexes() -> None:
    """Create the indexes the queries above rely on."""
    await collection.create_index([("user_id", 1), ("uploaded_at", -1)])
    await collection.create_index("doc_id", unique=True)
