from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.db import get_supabase

app = FastAPI(title="SnapSort")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "base.html", {"title": "SnapSort"})


@app.get("/health")
async def health():
    try:
        get_supabase()
        return JSONResponse({"status": "ok", "supabase": "connected"})
    except ValueError:
        return JSONResponse({"status": "ok", "supabase": "not configured"})
