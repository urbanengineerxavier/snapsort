from supabase import create_client, Client
from app.config import settings

supabase: Client | None = None
supabase_admin: Client | None = None


def get_supabase() -> Client:
    global supabase
    if supabase is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise ValueError("Supabase credentials not configured")
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    return supabase


def get_supabase_admin() -> Client:
    """Get Supabase client with service role key for admin operations like storage."""
    global supabase_admin
    if supabase_admin is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("Supabase service role key not configured")
        supabase_admin = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return supabase_admin
