import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
    APP_URL: str = os.getenv("APP_URL", "http://localhost:8000")

    # Notion OAuth
    NOTION_CLIENT_ID: str = os.getenv("NOTION_CLIENT_ID", "")
    NOTION_CLIENT_SECRET: str = os.getenv("NOTION_CLIENT_SECRET", "")

    @property
    def NOTION_REDIRECT_URI(self) -> str:
        return f"{self.APP_URL}/auth/notion/callback"


settings = Settings()
