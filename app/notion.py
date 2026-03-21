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


async def create_page(access_token: str, database_id: str, properties: dict, schema: dict) -> dict:
    """Create a new page in a Notion database with the given properties."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    # Convert extracted data to Notion property format
    notion_properties = _build_notion_properties(properties, schema)

    body = {
        "parent": {"database_id": database_id},
        "properties": notion_properties,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_BASE}/pages",
            headers=headers,
            json=body,
        )

    if response.status_code != 200:
        raise Exception(f"Failed to create page: {response.text}")

    return response.json()


def _build_notion_properties(data: dict, schema: dict) -> dict:
    """Convert extracted data to Notion API property format."""
    properties = {}

    # Common field name patterns for smart matching
    DESCRIPTION_NAMES = {"content", "description", "notes", "details", "summary", "text"}
    CLASSIFICATION_NAMES = {"type", "category", "classification", "tag", "label", "class"}
    FILES_NAMES = {"files", "files & media", "image", "images", "screenshot", "attachment", "media"}

    # Find schema fields - prioritize by name, then by type
    title_field = None
    rich_text_field = None
    classification_field = None
    classification_type = None
    files_field = None

    # First pass: find fields by common names
    for field_name, field_data in schema.items():
        field_type = field_data.get("type")
        field_name_lower = field_name.lower()

        if field_type == "title":
            title_field = field_name
        elif field_type == "rich_text" and field_name_lower in DESCRIPTION_NAMES:
            rich_text_field = field_name
        elif field_name_lower in CLASSIFICATION_NAMES and field_type in ("select", "rich_text"):
            # Support both select and text fields for classification
            classification_field = field_name
            classification_type = field_type
        elif field_type == "files" and field_name_lower in FILES_NAMES:
            files_field = field_name

    # Second pass: fall back to first field of each type if not found by name
    for field_name, field_data in schema.items():
        field_type = field_data.get("type")
        if field_type == "rich_text" and not rich_text_field:
            rich_text_field = field_name
        elif field_type == "select" and not classification_field:
            classification_field = field_name
            classification_type = "select"
        elif field_type == "files" and not files_field:
            files_field = field_name

    # Map our standard extracted fields to Notion schema
    if "title" in data and title_field:
        properties[title_field] = {"title": [{"text": {"content": str(data["title"])}}]}

    if "description" in data and rich_text_field:
        # Notion rich_text has 2000 char limit per block
        desc = str(data["description"])[:2000]
        properties[rich_text_field] = {"rich_text": [{"text": {"content": desc}}]}

    if "classification" in data and classification_field:
        if classification_type == "select":
            properties[classification_field] = {"select": {"name": str(data["classification"])}}
        else:
            properties[classification_field] = {"rich_text": [{"text": {"content": str(data["classification"])}}]}

    if "image_url" in data and files_field:
        properties[files_field] = {
            "files": [{"type": "external", "name": "screenshot", "external": {"url": str(data["image_url"])}}]
        }

    # Also handle any direct field matches for flexibility
    for key, value in data.items():
        if key in ("title", "description", "classification", "image_url"):
            continue  # Already handled above
        if key not in schema or value is None:
            continue

        prop_type = schema[key].get("type")

        if prop_type == "title":
            properties[key] = {"title": [{"text": {"content": str(value)}}]}
        elif prop_type == "rich_text":
            properties[key] = {"rich_text": [{"text": {"content": str(value)[:2000]}}]}
        elif prop_type == "number":
            try:
                properties[key] = {"number": float(value)}
            except (ValueError, TypeError):
                pass
        elif prop_type == "select":
            properties[key] = {"select": {"name": str(value)}}
        elif prop_type == "multi_select":
            if isinstance(value, list):
                properties[key] = {"multi_select": [{"name": str(v)} for v in value]}
            else:
                properties[key] = {"multi_select": [{"name": str(value)}]}
        elif prop_type == "date":
            properties[key] = {"date": {"start": str(value)}}
        elif prop_type == "checkbox":
            properties[key] = {"checkbox": bool(value)}
        elif prop_type == "url":
            properties[key] = {"url": str(value)}
        elif prop_type == "email":
            properties[key] = {"email": str(value)}
        elif prop_type == "phone_number":
            properties[key] = {"phone_number": str(value)}
        elif prop_type == "files":
            properties[key] = {
                "files": [{"type": "external", "name": "file", "external": {"url": str(value)}}]
            }

    return properties


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