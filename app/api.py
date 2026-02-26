from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from app.session import get_current_user
from app.notion import fetch_and_store_databases

router = APIRouter(prefix="/api")


@router.post("/databases/sync", response_class=HTMLResponse)
async def sync_databases(request: Request):
    """Re-fetch user's Notion databases and update Supabase."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = user.get("notion_access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No Notion token found")

    databases = await fetch_and_store_databases(str(user["id"]), access_token)

    # Return HTML partial for HTMX
    db_list = "".join(
        f'<div class="p-3 border rounded-lg">{db.get("icon", "📁")} {db["name"]}</div>'
        for db in databases
    )
    return f'<div class="grid gap-2">{db_list}</div>' if databases else '<p class="text-gray-500">No databases found</p>'