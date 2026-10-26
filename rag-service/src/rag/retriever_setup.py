"""
Vector store for users' uploaded documents, backed by Qdrant.

All users share one collection; every chunk carries its owner's user_id and
its document's doc_id in the metadata, and searches filter on user_id.
"""

import contextlib
import logging
import threading

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models

from src.core.config import settings
from src.llms.provider import get_embeddings

logger = logging.getLogger(__name__)

_store: QdrantVectorStore | None = None
_store_lock = threading.Lock()
# Embedded Qdrant isn't safe for concurrent use; a Qdrant server is.
_ops_lock = contextlib.nullcontext() if settings.QDRANT_URL else threading.Lock()


def _get_store() -> QdrantVectorStore:
    """Connect to Qdrant on first use, creating the collection if needed."""
    global _store
    with _store_lock:
        if _store is not None:
            return _store

        if settings.QDRANT_URL:
            client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=30)
        else:
            client = QdrantClient(path=settings.QDRANT_PATH)

        embeddings = get_embeddings()
        collection = settings.QDRANT_COLLECTION
        if not client.collection_exists(collection):
            dimension = len(embeddings.embed_query("dimension probe"))
            client.create_collection(
                collection,
                vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
            )
            logger.info("Created Qdrant collection '%s' (dimension %d)", collection, dimension)
        # Payload indexes only exist on a Qdrant server; embedded mode doesn't use them.
        # Creating an existing index is a no-op, so this also repairs an interrupted setup.
        if settings.QDRANT_URL:
            for field in ("metadata.user_id", "metadata.doc_id"):
                client.create_payload_index(collection, field, field_schema=models.PayloadSchemaType.KEYWORD)

        # Raises if the collection was created with a different embedding model.
        _store = QdrantVectorStore(client=client, collection_name=collection, embedding=embeddings)
        return _store


def _match(**fields: str) -> models.Filter:
    return models.Filter(must=[
        models.FieldCondition(key=f"metadata.{key}", match=models.MatchValue(value=value))
        for key, value in fields.items()
    ])


def add_documents(user_id: str, doc_id: str, chunks: list[Document]) -> None:
    """
    Store a document's chunks for a user.

    Args:
        user_id: Owner of the document.
        doc_id: Identifies the document, for later deletion.
        chunks: The document's chunks.
    """
    for chunk in chunks:
        chunk.metadata.update(user_id=user_id, doc_id=doc_id)
    store = _get_store()
    with _ops_lock:
        store.add_documents(chunks)
    logger.info("Stored %d chunks for user '%s'", len(chunks), user_id)


def search(user_id: str, query: str) -> list[Document]:
    """
    The user's chunks most similar to the query.

    Args:
        user_id: Whose documents to search.
        query: Text to search for.
    """
    store = _get_store()
    with _ops_lock:
        return store.similarity_search(query, k=settings.RETRIEVAL_K, filter=_match(user_id=user_id))


def delete_document(user_id: str, doc_id: str) -> None:
    """Delete all chunks of one of the user's documents."""
    store = _get_store()
    with _ops_lock:
        store.client.delete(
            store.collection_name,
            points_selector=models.FilterSelector(filter=_match(user_id=user_id, doc_id=doc_id)),
        )
