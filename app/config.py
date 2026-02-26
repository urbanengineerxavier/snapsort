import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
    APP_URL: str = os.getenv("APP_URL", "http://localhost:8000")


settings = Settings()
