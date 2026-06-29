# thinkingify

A calm, offline-first thinking platform built for a 9-year-old to encourage
deep thinking, reflection, and creativity instead of passive screen time.

## Structure

- [`ui/`](ui/) — Angular 19 frontend. Frontend-only V1:
  no auth, no backend, all state in localStorage. See [`ui/CLAUDE.md`](ui/CLAUDE.md)
  for architecture, design system, and current build status.
- [`api/`](api/) — placeholder for a future backend. Empty in V1 by design.

## Running locally

```bash
cd ui
nvm use   # pins Node 22 — Angular 19 doesn't yet support Node 24
npm install
npm start
```
