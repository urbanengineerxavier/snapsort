from typing import Any
from fastapi import Request, Response, Depends

from itsdangerous import URLSafeSerializer, BadSignature

from app.config import settings
from app.db import get_supabase

SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

serializer = URLSafeSerializer(settings.SECRET_KEY, salt="session")


def create_session(response: Response, user_id: str) -> None:
    """Set a signed session cookie with the user ID."""
    token = serializer.dumps({"user_id": user_id})
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )


def get_session_user_id(request: Request) -> str | None:
    """Read and verify the session cookie, return user_id or None."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    try:
        data = serializer.loads(token)
        return data.get("user_id")
    except BadSignature:
        return None


def clear_session(response: Response) -> None:
    """Delete the session cookie."""
    response.delete_cookie(key=SESSION_COOKIE_NAME)


def get_current_user(request: Request) -> dict[str, Any] | None:
    """FastAPI dependency to get the current logged-in user."""
    user_id = get_session_user_id(request)
    if not user_id:
        return None

    supabase = get_supabase()
    result = supabase.table("users").select("*").eq("id", user_id).execute()

    if not result.data:
        return None

    return result.data[0]
