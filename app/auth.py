import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.config import settings
from app.db import get_supabase
from app.session import create_session, clear_session
from app.notion import fetch_and_store_databases

router = APIRouter(prefix="/auth")

NOTION_AUTH_URL = "https://api.notion.com/v1/oauth/authorize"
NOTION_TOKEN_URL = "https://api.notion.com/v1/oauth/token"


@router.get("/notion")
async def notion_login():
    """Redirect user to Notion OAuth authorization page."""
    if not settings.NOTION_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Notion client ID not configured")

    params = {
        "client_id": settings.NOTION_CLIENT_ID,
        "response_type": "code",
        "owner": "user",
        "redirect_uri": settings.NOTION_REDIRECT_URI,
    }
    auth_url = f"{NOTION_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/notion/callback")
async def notion_callback(code: str | None = None, error: str | None = None):
    """Handle Notion OAuth callback, exchange code for access token."""
    if error:
        raise HTTPException(status_code=400, detail=f"Notion auth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            NOTION_TOKEN_URL,
            auth=(settings.NOTION_CLIENT_ID, settings.NOTION_CLIENT_SECRET),
            json={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.NOTION_REDIRECT_URI,
            },
            headers={"Content-Type": "application/json"},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange code: {response.text}",
        )

    token_data = response.json()
    access_token = token_data.get("access_token")
    workspace_id = token_data.get("workspace_id")
    workspace_name = token_data.get("workspace_name")

    # Create or update user in database
    supabase = get_supabase()

    # Check if user with this workspace already exists
    existing = supabase.table("users").select("id").eq(
        "notion_workspace_id", workspace_id
    ).execute()

    if existing.data:
        # Update existing user
        user_id = existing.data[0]["id"]
        supabase.table("users").update({
            "notion_access_token": access_token,
            "notion_workspace_name": workspace_name,
        }).eq("id", user_id).execute()
    else:
        # Create new user
        result = supabase.table("users").insert({
            "notion_access_token": access_token,
            "notion_workspace_id": workspace_id,
            "notion_workspace_name": workspace_name,
        }).execute()
        user_id = result.data[0]["id"]

    # Fetch and store user's Notion databases
    await fetch_and_store_databases(str(user_id), access_token)

    # Create session cookie and redirect to dashboard
    response = RedirectResponse(url="/dashboard", status_code=302)
    create_session(response, str(user_id))
    return response


@router.post("/logout")
async def logout():
    """Clear session and redirect to home."""
    response = RedirectResponse(url="/", status_code=302)
    clear_session(response)
    return response
