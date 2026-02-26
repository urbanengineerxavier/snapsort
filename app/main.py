from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

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
