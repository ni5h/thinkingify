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
    jwt_refresh_token_expire_days: int = 7

    google_client_id: str = ""

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_storage_bucket: str = "thinkingify"

    admin_emails: str = ""
    author_emails: str = ""
    learner_emails: str = ""

    cors_origins: str = "http://localhost:4200"

    @property
    def admin_emails_set(self) -> set[str]:
        return {e.strip().lower() for e in self.admin_emails.split(",") if e.strip()}

    @property
    def author_emails_set(self) -> set[str]:
        return {e.strip().lower() for e in self.author_emails.split(",") if e.strip()}

    @property
    def learner_emails_set(self) -> set[str]:
        return {e.strip().lower() for e in self.learner_emails.split(",") if e.strip()}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
