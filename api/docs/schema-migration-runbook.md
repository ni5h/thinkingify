# Thinkingify → sweet_pills Supabase migration (fresh start, keep proprietary content)

Move Thinkingify off its own Supabase project into the **sweet_pills** project
under a dedicated `thinkingify` Postgres schema, so the old project can be
deleted and its free-tier slot freed.

- **OLD** project (source, to be deleted): `ugruvuwnuekesxuphvsb` (ap-southeast-2)
- **NEW** project (target = sweet_pills): `lnllgwdjpwklhkswmlom` (ap-south-1)

## Decision: fresh start, content preserved in code

Neo's test data (blog/diary `content`, notes, companion chat, puzzle/brother
progress, family links, accounts) is **disposable** — not migrated. The only
**proprietary** data is the **23 curated Rowling topics** (explainer + narration
audio) and the **maths problems**. Both are now **version-controlled in the
repo** rather than migrated from the live DB:

- `app/seeds/topics.py` + `topics_data.json` — the 23 topics (audio URLs already
  point at the sweet_pills bucket).
- `app/seeds/topic_audio/*.mpeg` — the 20 narration files (durable backup).
- `app/seeds/math_problems.py` — the maths problems (pre-existing).
- `app/seeds/upload_topic_audio.py` — pushes the audio into Storage.

So there is **no production-data dump/restore and nothing touches the live DBs
by hand**. On deploy the container runs `alembic upgrade head` then the two
seeds (both idempotent), creating the `thinkingify` schema and populating the
proprietary content automatically.

## Cutover (mostly mobile-doable)

1. **Merge** the `feature/migrate-to-thinkingify-schema` branch to `main`
   (GitHub — mobile OK).

2. **Create the Storage bucket.** In the sweet_pills Supabase project → Storage →
   new **public** bucket named exactly `thinkingify`.

3. **Repoint Render** (`thinkingify-api` → Environment) and redeploy. Change only
   these; leave JWT/Google/Anthropic/CORS as they are:
   - `DATABASE_URL` → sweet_pills **transaction pooler (6543)** URL
   - `SUPABASE_URL` → `https://lnllgwdjpwklhkswmlom.supabase.co`
   - `SUPABASE_ANON_KEY` → sweet_pills anon key
   - `SUPABASE_SERVICE_ROLE_KEY` → sweet_pills service-role key
   - `SUPABASE_STORAGE_BUCKET` → keep `thinkingify`

   The redeploy auto-creates the `thinkingify` schema and seeds topics + maths.
   (sweet_pills' own `sweetpills` schema is untouched — verified.)

4. **Upload the topic audio** to the new bucket (one-time). Either:
   - with the sweet_pills service-role key available, run
     `python -m app.seeds.upload_topic_audio` (I can do this from the dev box if
     you paste the key), **or**
   - upload `app/seeds/topic_audio/*.mpeg` into the bucket under `topic-audio/`
     via the Supabase dashboard.

5. **Verify:** sign in at thinkingify.com; the Rowling room shows the 23 topics; a
   topic reader plays its audio; `GET /api/v1/topics/published` returns 23.
   Spot-check the sweet_pills app is unaffected.

6. **Delete the OLD Supabase project** (`ugruvuwnuekesxuphvsb`) to free the slot.

**Rollback:** until the OLD project is deleted, revert by pointing Render env
back at it. OLD is never mutated by this process, so it stays a clean fallback.

### Notes
- Both apps now share one Postgres instance + its connection pool / free-tier
  connection limits. Fine for personal projects.
- `thinkingify` schema isolation is via `MetaData(schema="thinkingify")` +
  schema-scoped enums + Alembic `version_table_schema` — mirrors how sweet_pills
  isolates under `sweetpills`. Verified locally: fresh migrate + seeds land all
  objects + content in `thinkingify`, coexisting with a `sweetpills` schema with
  no collision.
