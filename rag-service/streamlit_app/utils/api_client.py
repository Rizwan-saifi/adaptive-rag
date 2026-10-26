"""
API client for communicating with backend services.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

# Backend service URLs
RUST_BASE_URL = "http://localhost:8080/api"
PYTHON_BASE_URL = "http://127.0.0.1:8000"


def create_user(username: str, password: str, api_token: str) -> bool:
    """
    Create a new user account.

    Args:
        username: Username for the new account.
        password: Password for the new account.
        api_token: API token for authentication.

    Returns:
        True if user creation succeeds, False otherwise.
    """
    headers = {
        "X-API-TOKEN": api_token,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(
            f"{RUST_BASE_URL}/create_user",
            json={"username": username, "password": password},
            headers=headers,
        )

        logger.info("Calling /create_user, status code: %s", response.status_code)

        if response.status_code == 200:
            return True
        else:
            logger.error(
                "Create user failed: %s - %s",
                response.status_code,
                response.text
            )
            return False

    except requests.RequestException as e:
        logger.exception("Request to /create_user failed: %s", e)
        return False


def login_user(username: str, password: str, api_token: str) -> dict:
    """
    Authenticate user login.

    Args:
        username: Username to log in.
        password: Password for the user.
        api_token: API token for authentication.

    Returns:
        Response dictionary with JWT token if successful, None otherwise.
    """
    headers = {
        "X-API-TOKEN": api_token,
        "Content-Type": "application/json"
    }
    response = requests.post(
        f"{RUST_BASE_URL}/login",
        json={"username": username, "password": password},
        headers=headers,
    )
    logger.info("Calling /login, status code: %s", response.status_code)

    if response.status_code == 200:
        return response.json()

    return None


def get_api_token() -> str:
    """
    Get an API token for authentication.

    Returns:
        API token string if successful, None otherwise.
    """
    try:
        response = requests.post(f"{RUST_BASE_URL}/init", timeout=10)
    except requests.RequestException as e:
        logger.error("Request to /init failed: %s", e)
        return None
    logger.info("Calling /init, status code: %s", response.status_code)

    if response.status_code == 200:
        return response.json()["api_token"]

    return None


def query_backend(query: str, jwt_token: str) -> str:
    """
    Send a query to the RAG backend.

    Args:
        query: The user's query text.
        jwt_token: Login token; authenticates the user and identifies the chat session.

    Returns:
        Response text from the backend or error message.
    """
    url = f"{PYTHON_BASE_URL}/rag/query"
    print(f"[query_backend] Calling: {url}")

    response = requests.post(
        url,
        json={"query": query, "session_id": jwt_token},
        headers={"Authorization": f"Bearer {jwt_token}"},
        allow_redirects=False
    )

    if response.status_code == 200:
        return response.json()["result"]["content"]
    elif response.status_code == 401:
        return "Your session has expired. Please log out and log in again."
    else:
        return f"Error: {response.status_code} - {response.text}"


def document_upload_rag(file, description: str, jwt_token: str) -> bool:
    """
    Upload a document to the RAG system.

    Args:
        file: File object to upload.
        description: Description of the document.
        jwt_token: Login token identifying the document's owner.

    Returns:
        True if upload succeeds, False otherwise.
    """
    headers = {
        "X-Description": description,
        "Authorization": f"Bearer {jwt_token}",
    }
    url = f"{PYTHON_BASE_URL}/rag/documents/upload"

    if file:
        files = {"file": (file.name, file, file.type)}
        response = requests.post(url, files=files, headers=headers)
        print(response)

        if response.status_code == 200:
            return True

    return False
