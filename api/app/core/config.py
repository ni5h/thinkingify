from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Thinkingify API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Deliberately separate from `debug` — enabling the dev-login bypass
    # shouldn't also flip on FastAPI's traceback-in-500-responses behavior
    # or SQLAlchemy's SQL-echo logging, both real info-disclosure concerns
    # if this ever runs on a public deployment with debug=True too.
    allow_dev_login: bool = False

    database_url: str = ""

    jwt_secret: str = "dev-secret-change-me"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 30

    google_client_id: str = ""

    supabase_url: str = ""
    supabase_anon_key: str = ""
    # Storage writes go through this key server-side so they bypass the
    # storage.objects RLS policy — this app has its own JWT auth, not
    # Supabase Auth, so the anon key never carries an authenticated
    # session and RLS would reject every upload. Never sent to the client.
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "thinkingify"

    # Writing companion chat — Anthropic Claude Haiku, chosen over free-tier
    # alternatives specifically because Anthropic doesn't train on API
    # customer data by default, a real consideration for a child's writing.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"
    anthropic_timeout_seconds: float = 20.0

    cors_origins: str = "http://localhost:4200"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
