import uuid
from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse

from app.session import get_current_user
from app.notion import fetch_and_store_databases, create_page
from app.db import get_supabase, get_supabase_admin
from app.config import settings
from app.ai import extract_from_image

router = APIRouter(prefix="/api")

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


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

    # Return HTML partial for HTMX - only show databases in picker
    picker_dbs = [db for db in databases if db.get("is_in_picker")]
    db_list = "".join(
        f'<div class="p-3 border rounded-lg bg-white flex items-center gap-2"><span>{db.get("icon", "📁")}</span><span>{db["name"]}</span></div>'
        for db in picker_dbs
    )
    return f'<div class="grid gap-2">{db_list}</div>' if picker_dbs else '<p class="text-gray-500">No databases selected. Go to Settings to add databases.</p>'


@router.post("/databases/{db_id}/toggle", response_class=HTMLResponse)
async def toggle_database(request: Request, db_id: str):
    """Toggle a database's is_in_picker status."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    supabase = get_supabase()

    # Get current state
    result = supabase.table("databases").select("is_in_picker").eq("id", db_id).eq("user_id", user["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Database not found")

    current_state = result.data[0]["is_in_picker"]
    new_state = not current_state

    # Update
    supabase.table("databases").update({"is_in_picker": new_state}).eq("id", db_id).execute()

    # Return updated checkbox HTML
    checked = "checked" if new_state else ""
    return f'<input type="checkbox" {checked} hx-post="/api/databases/{db_id}/toggle" hx-swap="outerHTML" class="w-5 h-5 text-blue-600 rounded cursor-pointer">'


@router.post("/upload")
async def upload_image(request: Request, file: UploadFile = File(...)):
    """Upload an image to Supabase storage."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only images allowed.")

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    # Generate unique filename
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "png"
    filename = f"{user['id']}/{uuid.uuid4()}.{ext}"

    # Upload to Supabase storage (use admin client for storage permissions)
    supabase = get_supabase_admin()
    try:
        result = supabase.storage.from_("screenshots").upload(
            path=filename,
            file=content,
            file_options={"content-type": file.content_type}
        )
        # Check if upload returned an error
        if hasattr(result, 'error') and result.error:
            raise HTTPException(status_code=500, detail=f"Upload failed: {result.error}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    # Get public URL
    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/screenshots/{filename}"

    return JSONResponse({"url": public_url, "filename": filename})


@router.post("/route")
async def route_images(request: Request):
    """Extract data from images and create Notion pages."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = user.get("notion_access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No Notion token found")

    # Parse request body
    body = await request.json()
    image_urls = body.get("image_urls", [])
    database_id = body.get("database_id")
    classification = body.get("classification")

    if not image_urls:
        raise HTTPException(status_code=400, detail="No images provided")
    if not database_id:
        raise HTTPException(status_code=400, detail="No database selected")

    # Get database info
    supabase = get_supabase()
    db_result = supabase.table("databases").select("*").eq("id", database_id).eq("user_id", user["id"]).execute()
    if not db_result.data:
        raise HTTPException(status_code=404, detail="Database not found")

    database = db_result.data[0]
    notion_db_id = database["notion_database_id"]
    schema = database.get("schema", {})

    results = []
    for image_url in image_urls:
        try:
            # Extract data using OpenAI Vision
            extracted = await extract_from_image(image_url)

            # Add classification and image URL to extracted data
            if classification:
                extracted["classification"] = classification
            extracted["image_url"] = image_url

            # Create Notion page
            page = await create_page(access_token, notion_db_id, extracted, schema)

            results.append({
                "image_url": image_url,
                "success": True,
                "extracted": extracted,
                "notion_url": page.get("url"),
            })
        except Exception as e:
            results.append({
                "image_url": image_url,
                "success": False,
                "error": str(e),
            })

    return JSONResponse({
        "results": results,
        "database_name": database["name"],
    })