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

    # Public OAuth client id (not a secret — it's embedded in the frontend
    # bundle). Defaulted so sign-in works even where the env var is unset.
    google_client_id: str = "631847061926-a9g9rplpf07k17rfeu4n24b0d5dajduc.apps.googleusercontent.com"

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

    # --- Offline content pipeline (Phase 2, never served by the API) ---
    # Swappable generation adapters, selected by name so changing a model or
    # voice touches one adapter, not the pipeline. Defaults keep tests and a
    # keyless checkout working: text falls back to a deterministic stub, images
    # and TTS are stubbed (images deferred to a later provider; TTS runs only
    # post-review), and embeddings default to the dependency-free hash adapter
    # — a real run sets `pipeline_embedding_adapter=local` for the local model.
    pipeline_text_adapter: str = "claude"  # claude | stub
    pipeline_image_adapter: str = "svg"  # svg (Claude-drawn) | stub | (raster provider later)
    pipeline_tts_adapter: str = "stub"  # stub (post-review step)
    pipeline_embedding_adapter: str = "hash"  # local | hash
    # Local embedding model (model2vec static embeddings — CPU-only, torch-free)
    # used when pipeline_embedding_adapter=local. The private reference set is
    # embedded locally so its text never leaves the machine.
    pipeline_embedding_model: str = "minishlab/potion-base-8M"
    # Optional per-role model overrides; fall back to anthropic_model. The
    # critique pass should use a different model than generation where possible.
    pipeline_generation_model: str = ""
    pipeline_critique_model: str = ""
    # Dedupe: cosine similarity at/above this drops a generated item as a near
    # duplicate of another generated item or the private reference set.
    pipeline_dedupe_threshold: float = 0.88
    # Reading level: items above this Flesch-Kincaid grade are too hard for 9.
    # FK over-penalises necessary science vocab (e.g. "herbivore"), so the
    # ceiling sits a little above grade 4-5.
    pipeline_reading_grade_max: float = 6.5
    # Private reference intake (scans/olympiad banks). Gitignored; a test fails
    # if anything under it is tracked. Never committed, shown, or put in prompts.
    reference_dir: str = "private_reference"

    cors_origins: str = "http://localhost:4200"

    # Comma-separated emails that get the `admin` role on sign-in — the only
    # accounts allowed to author the curriculum (concept map). Everyone else
    # stays a learner. Sign-up is still open; this only grants authoring rights.
    admin_emails: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def admin_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.admin_emails.split(",") if e.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
