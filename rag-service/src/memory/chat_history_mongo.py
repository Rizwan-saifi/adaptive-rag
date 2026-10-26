"""
Chat history storage using MongoDB backend.
"""

from datetime import datetime, timezone
from typing import List, Optional

from langchain_core.messages import BaseMessage, messages_from_dict

from src.db.mongo_client import db

collection = db["chat_history"]


class ChatHistory:
    """Messages of one of a user's conversations, stored in MongoDB."""

    def __init__(self, user_id: str, conversation_id: str):
        """
        Args:
            user_id: Owner of the conversation.
            conversation_id: Identifies the conversation among the user's ones.
        """
        self.user_id = user_id
        self.conversation_id = conversation_id

    def _filter(self) -> dict:
        return {"user_id": self.user_id, "conversation_id": self.conversation_id}

    async def add_message(self, message: BaseMessage) -> None:
        """
        Save a message to MongoDB.

        Args:
            message: The message to save.
        """
        await collection.insert_one({
            **self._filter(),
            "type": message.type,
            "content": message.content,
            "timestamp": datetime.now(timezone.utc),
        })

    async def get_messages(self, limit: Optional[int] = None) -> List[BaseMessage]:
        """
        Load the conversation's messages, oldest first.

        Args:
            limit: Only return this many of the most recent messages.

        Returns:
            List of messages in chronological order.
        """
        if limit is not None and limit <= 0:
            return []
        # _id breaks ties between messages saved within the same millisecond
        cursor = collection.find(self._filter()).sort([("timestamp", -1), ("_id", -1)])
        if limit is not None:
            cursor = cursor.limit(limit)
        docs = list(reversed(await cursor.to_list(length=None)))

        return messages_from_dict([
            {"type": d["type"], "data": {"content": d["content"]}}
            for d in docs
        ])

    @staticmethod
    async def list_conversations(user_id: str, limit: int = 50) -> List[dict]:
        """
        The user's conversations, most recently active first.

        Returns:
            Dicts with conversation_id, title (the first question) and updated_at.
        """
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$sort": {"timestamp": 1, "_id": 1}},
            {"$group": {
                "_id": "$conversation_id",
                "title": {"$first": "$content"},
                "updated_at": {"$last": "$timestamp"},
            }},
            {"$sort": {"updated_at": -1}},
            {"$limit": limit},
        ]
        return [
            {"conversation_id": d["_id"], "title": d["title"], "updated_at": d["updated_at"]}
            async for d in collection.aggregate(pipeline)
        ]

    @staticmethod
    async def ensure_indexes() -> None:
        """Create the indexes the queries above rely on."""
        await collection.create_index([("user_id", 1), ("conversation_id", 1), ("timestamp", 1)])
