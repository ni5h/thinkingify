# thinkingify api

Thinkingify's backend: FastAPI + Supabase Postgres/Storage. Currently powers
the Blog module (Thinkingify Studio) — `/api/v1/content`, `/api/v1/auth`,
`/api/v1/uploads` — see
`ui/CLAUDE.md` for the full Phase 1 design/status. The other five modules
(Home, Puzzle, Learn, Journal, Progress) are still frontend-only/localStorage
and untouched by this backend.

## Local setup

1. Create a Supabase project (Postgres + Storage). Create a Google Cloud
   OAuth 2.0 Client ID (Web application) — only the Client ID is needed
   server-side, not the secret.
2. `cp .env.example .env` and fill in `DATABASE_URL` (use Supabase's
   Transaction Pooler connection string, port 6543), `GOOGLE_CLIENT_ID`,
   `SUPABASE_URL`/`SUPABASE_ANON_KEY`, `JWT_SECRET` (any long random string),
   and `ADMIN_EMAILS`/`AUTHOR_EMAILS` (comma-separated allow-lists — sign-in
   is rejected for any other email).
3. `poetry install`
4. `poetry run alembic upgrade head`
5. `poetry run uvicorn app.main:app --reload` — or `docker compose up` from
   the repo root, which also boots `ui/`.
6. `poetry run pytest` — runs against an in-memory SQLite DB, no Supabase
   connection needed for the test suite.

API docs at `/docs` once running.
