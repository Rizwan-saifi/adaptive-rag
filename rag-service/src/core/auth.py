"""
Authentication for API routes using JWTs issued by the auth gateway.
"""

import jwt
from fastapi import Header, HTTPException

from src.core.config import settings


def current_user(authorization: str = Header(None)) -> str:
    """
    FastAPI dependency returning the username from a valid Bearer JWT.

    Raises:
        HTTPException: 401 if the token is missing, invalid or expired.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        claims = jwt.decode(authorization[7:], settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired, please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return claims["sub"]
