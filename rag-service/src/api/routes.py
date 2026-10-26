"""
API routes for RAG operations.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Header, HTTPException
from fastapi.concurrency import run_in_threadpool
from langchain_core.messages import HumanMessage, AIMessage

from src.core.auth import current_user
from src.core.logger import logger
from src.memory.chat_history_mongo import ChatHistory
from src.models.query_request import QueryRequest
from src.rag.document_upload import documents
from src.rag.graph_builder import builder

router = APIRouter()


@router.post("/rag/query")
async def rag_query(req: QueryRequest, user_id: str = Depends(current_user)):
    """
    Process a RAG query and return the result.

    Args:
        req: The query request containing query text and session_id.
        user_id: Authenticated user, from the Bearer JWT.

    Returns:
        The generated response from the RAG pipeline.
    """
    #chat_history=ChatInMemoryHistory.get_session_history(req.token)
    # Namespace sessions by user so one user can't read another's history
    chat_history = ChatHistory.get_session_history(f"{user_id}:{req.session_id}")
    question = HumanMessage(content=req.query)
    messages = await chat_history.get_messages() + [question]

    # The graph makes blocking LLM calls; run it off the event loop so other
    # requests aren't stalled while it works.
    try:
        result = await run_in_threadpool(builder.invoke, {
            "messages": messages,
            "user_id": user_id,
        })
    except Exception:
        logger.exception("RAG pipeline failed")
        raise HTTPException(status_code=502, detail="The model call failed, please try again.")
    output_text = result["messages"][-1].content

    # Save the exchange only once it succeeded, so failures don't leave an
    # unanswered question in the history.
    await chat_history.add_message(question)
    await chat_history.add_message(AIMessage(content=output_text))

    return {"result": result["messages"][-1]}


@router.post("/rag/documents/upload")
async def upload_file(
    file: UploadFile = File(...),
    description: str = Header(..., alias="X-Description"),
    user_id: str = Depends(current_user),
):
    """
    Upload a document for RAG processing.

    Args:
        file: The file to upload (PDF or TXT).
        description: Document description provided via header.
        user_id: Authenticated user, from the Bearer JWT.

    Returns:
        Upload status.
    """
    status_upload = await run_in_threadpool(documents, user_id, description, file)
    return {"status": status_upload}

