import httpx
from app.db import get_supabase

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


async def fetch_and_store_databases(user_id: str, access_token: str) -> list[dict]:
    """Fetch user's Notion databases and store them in Supabase."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Notion-Version": NOTION_VERSION,
    }

    # Search for all databases the user has access to
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_BASE}/search",
            headers=headers,
            json={"filter": {"property": "object", "value": "database"}},
        )

    if response.status_code != 200:
        raise Exception(f"Failed to fetch databases: {response.text}")

    data = response.json()
    databases = data.get("results", [])

    supabase = get_supabase()

    # Clear existing databases for this user
    supabase.table("databases").delete().eq("user_id", user_id).execute()

    # Insert fetched databases
    stored = []
    for i, db in enumerate(databases):
        # Extract database info
        notion_db_id = db.get("id")
        title_parts = db.get("title", [])
        name = title_parts[0].get("plain_text", "Untitled") if title_parts else "Untitled"
        icon = _extract_icon(db.get("icon"))

        record = {
            "user_id": user_id,
            "notion_database_id": notion_db_id,
            "name": name,
            "icon": icon,
            "is_in_picker": True,
            "picker_order": i,
            "schema": db.get("properties", {}),
        }

        result = supabase.table("databases").insert(record).execute()
        stored.append(result.data[0])

    return stored


def _extract_icon(icon_data: dict | None) -> str | None:
    """Extract icon URL or emoji from Notion icon data."""
    if not icon_data:
        return None

    icon_type = icon_data.get("type")
    if icon_type == "emoji":
        return icon_data.get("emoji")
    elif icon_type == "external":
        return icon_data.get("external", {}).get("url")
    elif icon_type == "file":
        return icon_data.get("file", {}).get("url")

    return None