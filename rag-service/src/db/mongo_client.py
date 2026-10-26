"""
MongoDB client initialization.
"""

from motor.motor_asyncio import AsyncIOMotorClient

from src.core.config import settings

client = AsyncIOMotorClient(settings.MONGO_URL, tz_aware=True)
db = client[settings.MONGO_DB]
