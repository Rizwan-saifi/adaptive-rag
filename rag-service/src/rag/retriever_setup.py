"""
Retriever setup and per-user vector store management.
"""

import threading

from langchain_core.documents import Document
from langchain_core.tools import create_retriever_tool
from langchain_community.vectorstores import FAISS

from src.llms.provider import embeddings

# In-memory FAISS index and document descriptions per user (lost on restart).
# Qdrant support is currently disabled; see QDRANT_SETUP_GUIDE.md.
_user_stores: dict[str, FAISS] = {}
_user_descriptions: dict[str, list[str]] = {}
# Uploads run in worker threads; serialize changes to the stores.
_lock = threading.Lock()

# Shared placeholder for users who haven't uploaded anything yet.
_empty_store: FAISS | None = None


def retriever_chain(user_id: str, chunks: list[Document], description: str) -> bool:
    """
    Add document chunks to the user's vector store, creating it if needed.

    Args:
        user_id: Owner of the documents.
        chunks: Document chunks to store.
        description: Tool description of what the documents contain.

    Returns:
        Boolean indicating success of the operation.
    """
    try:
        with _lock:
            if user_id in _user_stores:
                _user_stores[user_id].add_documents(chunks)
            else:
                _user_stores[user_id] = FAISS.from_documents(documents=chunks, embedding=embeddings)
            _user_descriptions.setdefault(user_id, []).append(description)

        print(f"Stored {len(chunks)} chunks for user '{user_id}'")
        return True
    except Exception as e:
        print(f"Error storing documents in FAISS: {e}")
        return False


def _get_empty_store() -> FAISS:
    global _empty_store
    if _empty_store is None:
        _empty_store = FAISS.from_documents(
            documents=[Document(
                page_content="No documents have been uploaded yet. Please upload a document first.",
                metadata={"source": "initialization"},
            )],
            embedding=embeddings,
        )
    return _empty_store


def get_retriever(user_id: str):
    """
    Get a retriever tool over the given user's documents.

    Users without uploads get a placeholder store that says so.

    Args:
        user_id: Whose documents to search.

    Returns:
        A LangChain retriever tool.
    """
    store = _user_stores.get(user_id) or _get_empty_store()
    descriptions = _user_descriptions.get(user_id)
    description = "\n".join(descriptions) if descriptions else "No documents uploaded yet."

    return create_retriever_tool(
        store.as_retriever(),
        "retriever_customer_uploaded_documents",
        f"Use this tool **only** to answer questions about: {description}\n"
        "Don't use this tool to answer anything else."
    )
