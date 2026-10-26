"""
API client for communicating with backend services.

Failed calls raise ApiError with a message that can be shown to the user;
SessionExpired means the login token was rejected and the user must log in again.
"""

import json
import logging
import os
from typing import Iterator, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Backend service URLs
AUTH_BASE_URL = os.getenv("AUTH_GATEWAY_URL", "http://localhost:8080/api")
RAG_BASE_URL = os.getenv("RAG_API_URL", "http://127.0.0.1:8000")

# Seconds to wait for quick calls, and for calls that run the model or index a document
SHORT_TIMEOUT = 10
LONG_TIMEOUT = 300


class ApiError(Exception):
    """A backend call failed; the message is suitable for showing to the user."""


class SessionExpired(ApiError):
    """The login token was rejected; the user has to log in again."""

    def __init__(self):
        super().__init__("Your session has expired. Please log in again.")


def _error_message(response: requests.Response) -> str:
    """The error detail from a FastAPI or NestJS error response."""
    try:
        body = response.json()
    except ValueError:
        return f"Server error ({response.status_code})"
    detail = (body.get("detail") or body.get("message")) if isinstance(body, dict) else None
    if isinstance(detail, list):
        # Validation errors: FastAPI sends dicts with "msg", NestJS sends strings
        detail = "; ".join(d.get("msg", str(d)) if isinstance(d, dict) else str(d) for d in detail)
    return detail or f"Server error ({response.status_code})"


def _request(method: str, url: str, timeout: float = SHORT_TIMEOUT, **kwargs) -> requests.Response:
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
    except requests.RequestException as e:
        logger.error("Request to %s failed: %s", url, e)
        raise ApiError("Could not reach the server. Please try again.") from e
    logger.info("%s %s -> %s", method, url, response.status_code)
    return response


def _rag_request(method: str, path: str, jwt_token: str, **kwargs) -> requests.Response:
    """Call the RAG API as the logged-in user."""
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = _request(method, f"{RAG_BASE_URL}{path}", headers=headers, **kwargs)
    if response.status_code == 401:
        raise SessionExpired()
    if not response.ok:
        raise ApiError(_error_message(response))
    return response


def get_api_token() -> Optional[str]:
    """
    Get an API token for the auth gateway's signup and login endpoints.

    Returns:
        API token string if successful, None otherwise.
    """
    try:
        response = _request("POST", f"{AUTH_BASE_URL}/init")
    except ApiError:
        return None
    return response.json()["api_token"] if response.ok else None


def create_user(username: str, password: str, api_token: str) -> None:
    """
    Create a new user account.

    Raises:
        ApiError: If the account could not be created, e.g. the username is taken.
    """
    response = _request(
        "POST",
        f"{AUTH_BASE_URL}/create_user",
        json={"username": username, "password": password},
        headers={"X-API-TOKEN": api_token},
    )
    if not response.ok:
        raise ApiError(_error_message(response))


def login_user(username: str, password: str, api_token: str) -> str:
    """
    Log in and return the JWT identifying the user to the backends.

    Raises:
        ApiError: If the credentials are wrong or the gateway fails.
    """
    response = _request(
        "POST",
        f"{AUTH_BASE_URL}/login",
        json={"username": username, "password": password},
        headers={"X-API-TOKEN": api_token},
    )
    if response.status_code == 401:
        raise ApiError("Invalid username or password.")
    if not response.ok:
        raise ApiError(_error_message(response))
    return response.json()["jwt"]


def stream_answer(query: str, conversation_id: str, jwt_token: str) -> Iterator[str]:
    """
    Ask a question and yield the answer in pieces as it is generated.

    Raises:
        ApiError: If the backend fails, before or during the answer.
    """
    response = _rag_request(
        "POST",
        "/rag/query/stream",
        jwt_token,
        json={"query": query, "conversation_id": conversation_id},
        stream=True,
        timeout=LONG_TIMEOUT,
    )
    with response:
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            event = json.loads(line)
            if event["type"] == "token":
                yield event["content"]
            elif event["type"] == "error":
                raise ApiError(event["message"])


def list_conversations(jwt_token: str) -> list[dict]:
    """The user's conversations, most recently active first."""
    return _rag_request("GET", "/rag/conversations", jwt_token).json()


def get_conversation_messages(conversation_id: str, jwt_token: str) -> list[dict]:
    """A conversation's messages as dicts with role ("human"/"ai") and content."""
    return _rag_request("GET", f"/rag/conversations/{conversation_id}/messages", jwt_token).json()


def list_documents(jwt_token: str) -> list[dict]:
    """The user's uploaded documents, newest first."""
    return _rag_request("GET", "/rag/documents", jwt_token).json()


def upload_document(file, description: str, jwt_token: str) -> dict:
    """
    Upload a PDF or TXT document to search in later questions.

    Args:
        file: Streamlit UploadedFile.
        description: What the document is about.
        jwt_token: Login token identifying the document's owner.

    Returns:
        The stored document's record.
    """
    response = _rag_request(
        "POST",
        "/rag/documents/upload",
        jwt_token,
        files={"file": (file.name, file, file.type)},
        data={"description": description},
        timeout=LONG_TIMEOUT,
    )
    return response.json()["document"]


def delete_document(doc_id: str, jwt_token: str) -> None:
    """Delete one of the user's documents."""
    _rag_request("DELETE", f"/rag/documents/{doc_id}", jwt_token)
