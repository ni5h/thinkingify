# thinkingify

A calm, offline-first thinking platform built for a 9-year-old to encourage
deep thinking, reflection, and creativity instead of passive screen time.

## Structure

- [`ui/`](ui/) — Angular 20 frontend. Home/Puzzle/Learn/Journal/Progress are
  still frontend-only (localStorage, no auth). The Blog module —
  **Thinkingify Studio** — is backend-backed as of v0.1. See
  [`ui/CLAUDE.md`](ui/CLAUDE.md) for architecture, design system, and
  current build status.
- [`api/`](api/) — Thinkingify's FastAPI + Supabase (Postgres + Storage)
  backend, currently powering Thinkingify Studio. See
  [`api/README.md`](api/README.md) for local setup.

## Running locally

```bash
# frontend
cd ui
nvm use   # pins Node 22
npm install
npm start

# backend (needs a Supabase project + Google OAuth client — see api/README.md)
cd api
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload

# or both at once:
docker compose up
```
