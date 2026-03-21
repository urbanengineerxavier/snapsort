from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import List

from app.db import get_supabase
from app.auth import router as auth_router
from app.api import router as api_router
from app.session import get_current_user

app = FastAPI(title="SnapSort")
app.include_router(auth_router)
app.include_router(api_router)

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse(request, "home.html", {"title": "SnapSort", "user": user})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=302)

    # Fetch user's databases from Supabase
    supabase = get_supabase()
    result = supabase.table("databases").select("*").eq("user_id", user["id"]).order("picker_order").execute()
    databases = result.data or []

    return templates.TemplateResponse(request, "dashboard.html", {
        "title": "Dashboard",
        "user": user,
        "databases": databases,
    })


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=302)

    supabase = get_supabase()
    result = supabase.table("databases").select("*").eq("user_id", user["id"]).order("picker_order").execute()
    databases = result.data or []

    return templates.TemplateResponse(request, "onboarding.html", {
        "title": "Setup",
        "user": user,
        "databases": databases,
    })


@app.post("/onboarding/complete")
async def onboarding_complete(request: Request, database_ids: List[str] = Form(default=[])):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=302)

    supabase = get_supabase()

    # Set all databases to not in picker first
    supabase.table("databases").update({"is_in_picker": False}).eq("user_id", user["id"]).execute()

    # Then enable only the selected ones
    for i, db_id in enumerate(database_ids):
        supabase.table("databases").update({
            "is_in_picker": True,
            "picker_order": i,
        }).eq("id", db_id).eq("user_id", user["id"]).execute()

    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/health")
async def health():
    try:
        get_supabase()
        return JSONResponse({"status": "ok", "supabase": "connected"})
    except ValueError:
        return JSONResponse({"status": "ok", "supabase": "not configured"})


@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse(request, "privacy.html", {"title": "Privacy Policy"})


@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse(request, "terms.html", {"title": "Terms of Use"})
