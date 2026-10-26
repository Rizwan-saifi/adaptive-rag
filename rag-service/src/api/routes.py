"""
API routes for RAG operations.
"""

import json
import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import iterate_in_threadpool, run_in_threadpool
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage

from src.core.auth import current_user
from src.core.config import settings
from src.db import documents
from src.llms.provider import message_text
from src.memory.chat_history_mongo import ChatHistory
from src.models.query_request import QueryRequest
from src.rag.document_upload import load_and_split
from src.rag.graph_builder import ANSWER_NODES, rag_graph
from src.rag.retriever_setup import add_documents, delete_document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag")

MODEL_ERROR = "The model call failed, please try again."


async def _prepare(req: QueryRequest, user_id: str) -> tuple[ChatHistory, dict]:
    """The conversation's history and the graph input for a query."""
    history = ChatHistory(user_id, req.conversation_id)
    previous = await history.get_messages(limit=settings.MAX_HISTORY_MESSAGES)
    inputs = {"messages": previous + [HumanMessage(content=req.query)], "user_id": user_id}
    return history, inputs


async def _save(history: ChatHistory, query: str, answer: str) -> None:
    # Saved only once answered, so failures don't leave an unanswered question in the history.
    await history.add_message(HumanMessage(content=query))
    await history.add_message(AIMessage(content=answer))


@router.post("/query")
async def rag_query(req: QueryRequest, user_id: str = Depends(current_user)):
    """
    Answer a question and return the whole answer at once.

    Args:
        req: The question and the conversation it belongs to.
        user_id: Authenticated user, from the Bearer JWT.

    Returns:
        The answer, as {"result": {"type": "ai", "content": ...}}.
    """
    history, inputs = await _prepare(req, user_id)

    # The graph makes blocking LLM calls; run it off the event loop so other
    # requests aren't stalled while it works.
    try:
        result = await run_in_threadpool(rag_graph.invoke, inputs)
    except Exception:
        logger.exception("RAG pipeline failed")
        raise HTTPException(status_code=502, detail=MODEL_ERROR)
    answer = message_text(result["messages"][-1].content)

    await _save(history, req.query, answer)
    return {"result": {"type": "ai", "content": answer}}


def _event(kind: str, **fields) -> str:
    return json.dumps({"type": kind, **fields}) + "\n"


@router.post("/query/stream")
async def rag_query_stream(req: QueryRequest, user_id: str = Depends(current_user)):
    """
    Answer a question, streaming the answer as it is generated.

    The response is newline-delimited JSON events:
    {"type": "token", "content": ...} for each piece of the answer, then
    {"type": "done"} or {"type": "error", "message": ...}.
    """
    history, inputs = await _prepare(req, user_id)

    async def events():
        streamed = False
        final_state = None
        try:
            stream = rag_graph.stream(inputs, stream_mode=["messages", "values"])
            async for mode, data in iterate_in_threadpool(stream):
                if mode == "values":
                    final_state = data
                    continue
                chunk, metadata = data
                # Token chunks from the answering nodes; other nodes' model calls are internal.
                if isinstance(chunk, AIMessageChunk) and metadata.get("langgraph_node") in ANSWER_NODES:
                    text = message_text(chunk.content)
                    if text:
                        streamed = True
                        yield _event("token", content=text)
        except Exception:
            logger.exception("RAG pipeline failed")
            yield _event("error", message=MODEL_ERROR)
            return

        answer = message_text(final_state["messages"][-1].content)
        if not streamed:
            # The model didn't stream; send the answer in one piece.
            yield _event("token", content=answer)
        await _save(history, req.query, answer)
        yield _event("done")

    return StreamingResponse(events(), media_type="application/x-ndjson")


@router.get("/conversations")
async def list_conversations(user_id: str = Depends(current_user)):
    """The user's conversations, most recently active first."""
    return await ChatHistory.list_conversations(user_id)


@router.get("/conversations/{conversation_id}/messages")
async def conversation_messages(conversation_id: str, user_id: str = Depends(current_user)):
    """The messages of one of the user's conversations, oldest first."""
    messages = await ChatHistory(user_id, conversation_id).get_messages()
    return [{"role": m.type, "content": m.content} for m in messages]


@router.post("/documents/upload")
async def upload_file(
    file: UploadFile = File(...),
    description: str = Form(..., min_length=1, max_length=300),
    user_id: str = Depends(current_user),
):
    """
    Upload a PDF or TXT document to search in later questions.

    Args:
        file: The file to upload.
        description: What the document is about.
        user_id: Authenticated user, from the Bearer JWT.

    Returns:
        The stored document's record.
    """
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Files can be at most {settings.MAX_UPLOAD_MB} MB")

    filename = file.filename or ""
    try:
        chunks = await run_in_threadpool(load_and_split, filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not chunks:
        raise HTTPException(status_code=400, detail="No text found in the file")

    doc_id = uuid.uuid4().hex
    try:
        await run_in_threadpool(add_documents, user_id, doc_id, chunks)
    except Exception:
        logger.exception("Storing document chunks failed")
        raise HTTPException(status_code=502, detail="Could not index the document, please try again.")

    record = await documents.add(user_id, doc_id, filename, description, len(chunks))
    return {"status": True, "document": record}


@router.get("/documents")
async def list_documents(user_id: str = Depends(current_user)):
    """The user's uploaded documents, newest first."""
    return await documents.list_for_user(user_id)


@router.delete("/documents/{doc_id}")
async def remove_document(doc_id: str, user_id: str = Depends(current_user)):
    """Delete one of the user's documents so it is no longer searched."""
    if not await documents.get(user_id, doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    await run_in_threadpool(delete_document, user_id, doc_id)
    await documents.delete(user_id, doc_id)
    return {"status": "deleted"}
