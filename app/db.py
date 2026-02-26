from supabase import create_client, Client
from app.config import settings

supabase: Client | None = None


def get_supabase() -> Client:
    global supabase
    if supabase is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise ValueError("Supabase credentials not configured")
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    return supabase
