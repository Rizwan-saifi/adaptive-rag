"""
Main FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.db import documents
from src.memory.chat_history_mongo import ChatHistory

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ChatHistory.ensure_indexes()
    await documents.ensure_indexes()
    yield


app = FastAPI(title="Adaptive RAG API", lifespan=lifespan)
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {"message": "Adaptive RAG API is running"}
