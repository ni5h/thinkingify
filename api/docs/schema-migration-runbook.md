# Thinkingify → sweet_pills Supabase migration (schema: `thinkingify`)

Move the Thinkingify database out of its own Supabase project into the
**sweet_pills** project under a dedicated `thinkingify` Postgres schema, so the
old project can be deleted and its free-tier slot freed.

- **OLD** project (source, to be decommissioned): `ugruvuwnuekesxuphvsb` (ap-southeast-2)
- **NEW** project (target = sweet_pills): `lnllgwdjpwklhkswmlom` (ap-south-1)

The schema-aware code (models in `thinkingify` schema, `alembic/env.py`) is
already merged. The steps below are the **one-time cutover you run** — they
touch the live databases and Supabase Storage. Do them in a short maintenance
window. Nothing here is run by CI or the app.

Get connection strings from each Supabase dashboard → **Connect**:
- **Direct connection (port 5432)** for `pg_dump`/`pg_restore` — the pooler
  (6543) does not work with pg_dump. Call these `OLD_DIRECT` / `NEW_DIRECT`.
- The app keeps using the **Transaction pooler (6543)** URL (that's what goes in
  Render `DATABASE_URL`).

---

## 1. Pre-flight

- [ ] Confirm the schema-aware code is deployed-ready (merged to `main`) but
  **do not repoint Render yet**.
- [ ] Put the backend into a brief maintenance window (Render → `thinkingify-api`
  → scale to 0, or just accept a few minutes of read-only/failed writes — it's a
  personal app). This prevents new writes to OLD during the dump.
- [ ] `pg_dump`/`pg_restore`/`psql` available locally (Postgres client tools).

## 2. Move OLD prod into a `thinkingify` schema

OLD is being decommissioned, so mutating it in place is fine. Run the generated
move script (`api/docs/cutover_move.sql`, reproduced below) against **OLD_DIRECT**.
It moves all 16 enums + 18 tables + `alembic_version` from `public` to
`thinkingify` in one transaction.

```bash
psql "$OLD_DIRECT" -f api/docs/cutover_move.sql
```

Sanity check (should show 19 base tables incl. alembic_version, 16 enums):
```bash
psql "$OLD_DIRECT" -tAc "select count(*) from information_schema.tables where table_schema='thinkingify';"
psql "$OLD_DIRECT" -tAc "select version_num from thinkingify.alembic_version;"   # -> 0020
```

## 3. Dump the schema from OLD

```bash
pg_dump "$OLD_DIRECT" -n thinkingify --no-owner --no-privileges -Fc -f thinkingify.dump
```

## 4. Restore into NEW (sweet_pills)

Lands the `thinkingify` schema alongside the untouched `sweetpills` and `public`
schemas — no collisions (same table names live in different schemas; verified).

```bash
pg_restore --no-owner --no-privileges -d "$NEW_DIRECT" thinkingify.dump
```

Verify:
```bash
psql "$NEW_DIRECT" -tAc "select count(*) from thinkingify.content;"          # your real row count
psql "$NEW_DIRECT" -tAc "select version_num from thinkingify.alembic_version;"  # -> 0020
psql "$NEW_DIRECT" -tAc "select nspname from pg_namespace where nspname in ('public','sweetpills','thinkingify') order by 1;"
```

## 5. Storage: bucket + objects

Buckets are project-scoped (and free — not the constrained resource).

- [ ] In the **sweet_pills** Supabase dashboard → Storage → create a **public**
  bucket named exactly `thinkingify`.
- [ ] Copy objects from OLD project's `thinkingify` bucket → NEW project's
  `thinkingify` bucket. Options:
  - Supabase CLI: `supabase storage cp --recursive ss://thinkingify ./tmp` from
    OLD (linked), then `supabase storage cp --recursive ./tmp ss://thinkingify`
    into NEW (linked); or
  - a short script using each project's service-role key + the storage API.
    (Object count is small — feature images, diary photos, topic audio.)

## 6. Rewrite embedded URLs (old project ref → new)

Stored URLs embed the OLD project domain; rewrite them in the NEW DB. Discover
first, then update:

```sql
-- discovery (how many rows reference the old host)
select 'content.feature_image_url' col, count(*) from thinkingify.content
  where feature_image_url like '%ugruvuwnuekesxuphvsb.supabase.co%'
union all select 'users.avatar_url', count(*) from thinkingify.users
  where avatar_url like '%ugruvuwnuekesxuphvsb.supabase.co%'
union all select 'topics.audio_url', count(*) from thinkingify.topics
  where audio_url like '%ugruvuwnuekesxuphvsb.supabase.co%'
union all select 'content.content_markdown', count(*) from thinkingify.content
  where content_markdown like '%ugruvuwnuekesxuphvsb.supabase.co%'
union all select 'topics.explainer_markdown', count(*) from thinkingify.topics
  where explainer_markdown like '%ugruvuwnuekesxuphvsb.supabase.co%';

-- rewrite (only matches the old Supabase host, so Google-hosted avatars are safe)
update thinkingify.content set feature_image_url =
  replace(feature_image_url, 'ugruvuwnuekesxuphvsb.supabase.co', 'lnllgwdjpwklhkswmlom.supabase.co')
  where feature_image_url like '%ugruvuwnuekesxuphvsb.supabase.co%';
update thinkingify.users set avatar_url =
  replace(avatar_url, 'ugruvuwnuekesxuphvsb.supabase.co', 'lnllgwdjpwklhkswmlom.supabase.co')
  where avatar_url like '%ugruvuwnuekesxuphvsb.supabase.co%';
update thinkingify.topics set audio_url =
  replace(audio_url, 'ugruvuwnuekesxuphvsb.supabase.co', 'lnllgwdjpwklhkswmlom.supabase.co')
  where audio_url like '%ugruvuwnuekesxuphvsb.supabase.co%';
update thinkingify.content set content_markdown =
  replace(content_markdown, 'ugruvuwnuekesxuphvsb.supabase.co', 'lnllgwdjpwklhkswmlom.supabase.co')
  where content_markdown like '%ugruvuwnuekesxuphvsb.supabase.co%';
update thinkingify.topics set explainer_markdown =
  replace(explainer_markdown, 'ugruvuwnuekesxuphvsb.supabase.co', 'lnllgwdjpwklhkswmlom.supabase.co')
  where explainer_markdown like '%ugruvuwnuekesxuphvsb.supabase.co%';
```

## 7. Repoint config → sweet_pills project

Update **Render** (`thinkingify-api` → Environment) and your local `api/.env`:

- `DATABASE_URL` → sweet_pills **Transaction pooler (6543)** URL
- `SUPABASE_URL` → `https://lnllgwdjpwklhkswmlom.supabase.co`
- `SUPABASE_ANON_KEY` → sweet_pills anon key
- `SUPABASE_SERVICE_ROLE_KEY` → sweet_pills service-role key
- `SUPABASE_STORAGE_BUCKET` → keep `thinkingify`

Then trigger a redeploy (or scale the backend back up).

## 8. Verify prod, then decommission

- [ ] Sign in at thinkingify.com (writes/reads `thinkingify.users`).
- [ ] Blog list, a diary entry, and a topic reader load.
- [ ] An **existing image renders** (URL rewrite worked) and a **new upload**
  succeeds (new bucket).
- [ ] Spot-check the **sweet_pills** app itself — unaffected.
- [ ] Read-only probes: `https://api.thinkingify.com/api/v1/content/published`
  and `/docs` return 200.

**Rollback:** until the OLD project is deleted, revert by pointing Render env
back at the OLD project. Keep OLD alive ~a day after cutover looks green.

- [ ] Once confirmed stable: **delete the OLD Supabase project** (`ugruvuwnuekesxuphvsb`)
  to free the slot. Done.

---

### Notes
- Both apps now share one Postgres instance and its connection pool / free-tier
  connection limits. Fine for personal projects; keep in mind if either app
  starts exhausting connections.
- Dumps **must** use the direct 5432 endpoint (the 6543 pooler breaks pg_dump).
- The move/dump/restore mechanics were dry-run locally end-to-end (including
  coexistence with a `sweetpills` schema and a same-named `users` table) before
  this runbook was written.
