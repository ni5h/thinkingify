# Thinkingify — Claude Code Context

## Thinkingify Studio v0.1 — Phase 1 (last updated 2026-07-07)

The Blog module has been rebuilt as **Thinkingify Studio**: a real FastAPI +
Supabase (Postgres + Storage) backend replaces localStorage for blog content
only. See `thinkingify/api/` (new) and the plan at the time this was built
for full design rationale. Auth pattern ported from the sibling `sweet_pills`
repo (Google Identity Services + a Studio-issued JWT, not Supabase GoTrue
Auth), adapted to add an email allow-list (`ADMIN_EMAILS`/`AUTHOR_EMAILS`) —
sign-in itself is rejected with 403 for any email not on the list, since
Studio only ever has Admin/Author accounts, never open signup.

**Code-complete and verified as far as possible without live credentials:**
backend `pytest` suite (28 tests: allow-list resolution, full status
state-machine incl. illegal-transition 409s, soft delete, slug collisions,
author/admin scoping) passes; a full API smoke test against an in-memory DB
exercised the entire lifecycle end-to-end (sign-in → create → submit →
publish → public listing → slug lookup → archive → republish → soft delete)
through the real FastAPI routes. Frontend builds clean on both `development`
and `production` configs post-upgrade. **Not yet verified:** real Google
sign-in, a real Supabase-hosted Postgres/Storage, and `docker compose up` —
all require a live Supabase project + Google OAuth client, which weren't
available in the environment this was built in (Supabase project creation
and Google Cloud OAuth client are explicitly the user's own setup step; fill
in `api/.env` from `api/.env.example` and `ui/src/environments/environment.ts`
`googleClientId` once those exist, then re-run the exit-criteria checklist).

**Angular upgraded 19.2 → 20.3** as part of this work (last step, after the
API-backed conversion was verified, to avoid debugging two moving targets at
once). `ng update @angular/core@20 @angular/cli@20` ran clean, one
type-narrowing fix needed in the new dashboard component, no other breakage.

**New backend `api/`** (Poetry, Python 3.11, FastAPI, SQLAlchemy async +
asyncpg, Alembic, layered `router → service → model`, mirrors `sweet_pills`'s
structure): `users` (google_sub/email/role, allow-list gated) and `content`
(blog posts — `draft → pending_review → published ⇄ archived`, soft delete
via `deleted_at`, unique `slug`) tables; `/api/v1/auth/*`, `/api/v1/content/*`,
`/api/v1/uploads/feature-image` endpoints; Docker + `docker-compose.yml` for
local dev (no local Postgres container — DB is Supabase-hosted; no
Redis/Celery — not needed for this scope).

**Frontend IA change:** authenticated post management moved from
`/blog/manage*` to `/studio*` (`/studio` dashboard, `/studio/posts` list,
`/studio/posts/new`, `/studio/posts/:id/edit`, `/studio/login`), gated by
`authGuard`/`noAuthGuard`. Public reader routes (`/blog`, now `/blog/:slug`
— slug replaces id) are unchanged in spirit, just API-backed. `BlogService`
converted from synchronous localStorage-backed computed signals to
`httpResource()` for reads + async `HttpClient` writes (each write
`.reload()`s the relevant resource — the one real architectural loss vs.
localStorage's fully-automatic derivation). TipTap editor, toolbar, and the
warm/rounded design system were preserved verbatim; net-new in the editor:
autosave (debounced `PATCH` on existing drafts), word count, reading time.
Feature image upload now goes through a real backend-proxied endpoint to
Supabase Storage (client still does the canvas resize/JPEG-compress pass
first, now producing a `Blob` for multipart upload instead of a data URI).

**Explicitly deferred** (named in the original plan, not designed/built):
categories, tags, full Media Library (browse/search/reuse assets), homepage
redesign (hero/philosophy/featured), settings, analytics, migrating the
other five modules to a backend, and choosing a real production host for the
API (Phase 1's deliverable is "runs via `docker compose up`," not a live URL).

**Untouched by this work:** `/`, `/home`, `/puzzle`, `/learn`, `/journal`,
`/progress` — still exactly the localStorage/`StorageService`-backed modules
described below. `AppState` no longer includes `blogPosts` (removed; blog
content lives in Postgres now, not the local state blob).

## Build status (last updated 2026-06-29)

**Phase 1 (Foundation) is complete and verified.** `ng build` and `ng serve`
both run clean; navigation across all six routes confirmed in a real browser
at desktop and mobile widths (screenshots via headless Chrome).

**Project restructured and pushed to GitHub:** the repo root is now
`thinkingify/` (renamed from `thinking_platform/`), with this Angular app
living at `thinkingify/ui/` and `thinkingify/api/` as an empty placeholder
for the future backend. Public repo: https://github.com/ni5h/thinkingify.
Deployed via GitHub Actions (`.github/workflows/deploy-ui.yml`) to GitHub
Pages at https://ni5h.github.io/thinkingify/ — base-href is `/thinkingify/`
and there's a build-step copy of `index.html` to `404.html` for SPA routing
fallback. The Angular project identifier and `package.json` name were
renamed from `mental-models-gym` to `thinkingify-ui` to match; build output
is now at `dist/thinkingify-ui/browser`.

Done:
- Angular 19 project at `ui/` (Node 22 pinned via `.nvmrc` — Node 24 is not
  yet supported by Angular and was the default on this machine;
  `source ~/.nvm/nvm.sh && nvm use` before running anything)
- Tailwind v3 configured with the palette/fonts/animation tokens below
- `core/models/index.ts` — all interfaces incl. `AppState.activityDates`
- `StorageService` (`core/services/storage.service.ts`) — state held as a
  signal, `update()`/`save()`, plus `exportState()`/`importState()`
- `ProgressService` — all stats as `computed()` off `activityDates`/arrays,
  nothing persisted directly (streak math lives in `progress.service.ts`)
- `JournalService` — signals CRUD, calls `recordActivityToday()` on save
- App shell (`layout/shell`, `layout/nav`) — desktop sidebar / mobile bottom
  nav, six lazy routes wired in `app.routes.ts`
- Placeholder components for Home, Puzzle, Learn, Journal, Progress (just a
  heading + "Phase N builds this here" — not real implementations yet)
- **Blog module (built out of phase order, per explicit request):**
  `BlogService` (`core/services/blog.service.ts`) — full status workflow
  (`create`/`update`/`submitForReview`/`backToDraft`/`publish`/`archive`/
  `republish`/`delete`) plus `published`/`all` computed signals.
  `core/utils/image.ts` — client-side resize/JPEG-compress for cover images.
  Five routes under `features/blog/`: `blog-home.component.ts` (`/blog`,
  published only), `blog-post.component.ts` (`/blog/:id`, renders markdown
  via `marked` into `[innerHTML]` — Angular's default sanitizer handles the
  XSS concern), `blog-manage.component.ts` (`/blog/manage`, every post +
  status-appropriate action buttons), `blog-editor.component.ts`
  (`/blog/manage/new` and `/blog/manage/:id/edit`, **Confluence-style WYSIWYG
  editor via TipTap** — see below). Markdown content styling lives in a
  `.markdown-content` class in `styles.css` (no `@tailwindcss/typography`
  dependency added). Verified end-to-end in a real browser: create → submit
  → publish → public listing → detail page, plus cover image upload and
  localStorage persistence across reload.
- **Blog WYSIWYG editor (explicit user request, overrides the "no rich-text
  toolbar" rule below for this one screen):** `blog-editor.component.ts` now
  mounts a TipTap (`@tiptap/core`, `@tiptap/starter-kit`, `@tiptap/markdown`,
  `@tiptap/extension-placeholder`) editor directly on a template ref div in
  `ngAfterViewInit`, destroyed in `ngOnDestroy`. The official `Markdown`
  extension reads/writes markdown directly (`contentType: 'markdown'` on
  load, `editor.getMarkdown()` on save) so `BlogPost.contentMarkdown` stays
  the storage format with no HTML conversion layer — `BlogService` and the
  public `/blog/:id` `marked`-based rendering are unchanged. A plain
  text-label toolbar (B / I / S / H2 / H3 / bullet+numbered list / Quote /
  Code / Link) drives `editor.chain().focus().toggleX().run()` commands;
  active-state styling is tracked via a signal synced on TipTap's
  `onUpdate`/`onSelectionUpdate`. The Link button uses `window.prompt()`
  (same native-dialog precedent as the delete `confirm()` in
  `blog-manage.component.ts`) rather than a custom modal.
- **Vision homepage + collapsible sidebar (explicit user request):** root
  path `/` now loads `features/vision/vision.component.ts`, a static
  mission/overview page (hero, "why this exists" blurb, a 6-card module
  overview linking into each route) — reached via the sidebar wordmark, not
  one of the 6 module tabs. `/home` is unchanged (still the Phase 2
  dashboard placeholder). `layout/nav/nav.component.ts` gained a hamburger
  toggle (`collapsed` signal, local UI state only — not persisted) that
  shrinks the desktop sidebar to an icon-only rail; the mobile bottom nav is
  unaffected.
- **"Warm & rounded" visual refresh (explicit user request):** re-skinned
  Shell/Nav, the full Blog module, and all 5 placeholder pages from the old
  flat/left-border-accent look to rounded corners + soft shadows (see Design
  rules above). Added `shared/components/icon/icon.component.ts`, a dumb
  `app-icon` component with one inline SVG per nav item, used in both the
  sidebar/mobile nav and on each placeholder page's "coming soon" card. No
  `tailwind.config.js` changes were needed — the refresh uses Tailwind's
  existing stock radius/shadow scale.

Not started yet — **Phase 2: Home Dashboard**
(`features/home/home.component.ts`: greeting, streak badge, today's
puzzle/lesson quick-action cards, journal preview), then Phases 3–5 (Puzzle,
Learn, Journal), then Progress, per the module descriptions below.
`assets/data/puzzles.json` and `assets/data/lessons.json` have not been
created/seeded yet.

Per the original brief: confirm with the user before starting each new phase
rather than running straight through all of them.

## What this is
A frontend-only Angular 19 educational app for a 9-year-old child (Neo).
Core philosophy: use technology to encourage less screen time and more thinking.

## Stack
- Angular 19, standalone components, signals (no RxJS for app state)
- Tailwind CSS v3
- No backend. No auth. No database.
- All seed data in src/assets/data/*.json
- All persisted state in localStorage via StorageService

## Architecture rules
1. No component touches localStorage directly — always go through StorageService.
2. All services use signals and computed(), not Subjects or BehaviorSubjects.
3. All routes are lazy-loaded standalone components (`loadComponent`).
4. Shared UI components (`shared/components/`) are dumb — `@Input()`/`@Output()` only,
   no service injection.
5. Feature components are smart — they inject services directly.
6. HttpClient is used only to load local JSON data files, never external APIs.

## State model
Single localStorage key holds the entire `AppState`:
- `journalEntries`, `solvedPuzzleIds`, `completedLessonIds`, `blogPosts`
- `activityDates: string[]` — one distinct YYYY-MM-DD entry per day with ANY
  qualifying activity (puzzle solved, lesson completed, or journal entry saved).

**Do not persist derived counts or streaks.** `currentStreak`, `longestStreak`,
`totalDaysLearned`, `articlesWritten`, `puzzlesSolved.length`, `lessonsCompleted.length`,
and `questionsAsked` (count of journal entries with a non-empty
"questions I still have" field) are all `computed()` signals in `ProgressService`,
derived from the raw arrays above. This is intentional — it removes an entire class
of "forgot to update the counter" bugs and is the only way streak math stays correct.

`AppState` includes a `version` field. Bump it if you change any persisted shape,
and write a migration step in `StorageService` rather than assuming old data matches
the new interface.

## Design rules
1. Palette: ink #1C1917, paper #FAFAF7, cloud #F0EFE9, moss #4A7C59,
   moss-dark #2E5238, amber #D97706, muted #78716C.
2. Fonts: Fraunces (display/headings), DM Sans (body/labels/buttons),
   DM Mono (numbers — puzzle grids, stats, dates).
3. "Warm & rounded" look: soft shadows (`shadow-sm`/`shadow-md`, Tailwind's
   stock scale) and rounded corners (`rounded-lg`/`rounded-xl`/`rounded-2xl`,
   also Tailwind stock — `tailwind.config.js` is untouched) everywhere.
   Still no modals, no loading spinners (data is local — if something needs
   a spinner, reconsider the architecture), no looping/bouncing animations,
   no emojis in UI chrome.
4. Buttons and inputs are rounded pills/blocks (see button variants below),
   not left-border accents. `border-l-4` is preserved in exactly two
   non-button places: the active desktop sidebar nav indicator, and
   markdown blockquotes.
5. The only animation is `slideUp` on page entry (translateY 8px→0, opacity 0→1, 300ms ease-out).
6. The Journal module is the most important screen in the app — it must feel like
   a notebook page, not a form: generous line-height, minimal chrome, plain textareas.

### Button variants
- Primary: `rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors`
- Secondary: `rounded-xl border border-cloud bg-paper px-5 py-2.5 text-sm font-medium text-ink hover:border-moss hover:bg-cloud/60 transition-colors`
- Ghost: `rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors`
- Small inline toggle/pill (toolbar buttons, row actions): `rounded-lg`
  variants, active state `bg-moss/10 text-moss-dark`, a destructive/warning
  variant uses `bg-amber/10 text-amber`.

### Cards
`rounded-2xl border border-cloud bg-white shadow-sm` (add `overflow-hidden`
when a card wraps an image so corners clip cleanly).

### Inputs
`rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none
focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors`.

### Icons
`shared/components/icon/icon.component.ts` — a dumb standalone `app-icon`
component (`@Input({ required: true }) name: IconName`, `@Input() size`)
with one inline `<svg>` per nav item (`home`/`puzzle`/`learn`/`journal`/
`blog`/`progress`), colored via `currentColor` from the parent's `text-*`
class. Used in the sidebar/mobile nav and on each placeholder page's
"coming soon" card.

## Modules (V1)
1. **Home** — daily dashboard: greeting, streak, today's puzzle/lesson, journal preview.
2. **Puzzle** — one puzzle at a time from `assets/data/puzzles.json`, hint toggle,
   case-insensitive/trimmed answer check, solved state in StorageService.
3. **Learn** — today's lesson via `lessons[dayOfYear % lessons.length]`, ends in a
   prominent pause prompt ("Close the laptop. Think about this.") linking to journal.
4. **Journal** — six fixed reflection prompts, auto-save on blur, plain textareas only.
5. **Progress** — seven stat cards + a plain-text recent-activity timeline. No charts,
   no percentages, no comparisons to anyone else.
6. **Blog** — Neo's own publishing space. See below.

### Blog module specifics
- Same-device, localStorage-only — no backend, no real access control. The
  "dad approves" review step is a *workflow status*, not an auth gate: anyone on
  this device can see every action button, the status just controls what shows up
  on the public-style `/blog` view.
- Status lifecycle: `draft → pending_review → published`, plus `archived` for
  unpublish. Editing a published post updates it live — no re-review required for edits,
  only for the first submission, to keep friction low.
- `/blog` — published posts only, styled like a real blog homepage.
- `/blog/manage` — every post regardless of status, with status badge + actions.
- `/blog/manage/new`, `/blog/manage/:id/edit` — a TipTap-based WYSIWYG editor
  (the one documented exception to "no rich-text toolbar"/"no rich text
  editor" below). Storage format is still plain markdown — see the Done
  notes above for how the round-trip works. The public `/blog/:id` page
  still renders that markdown with `marked`, sanitizing the rendered HTML
  before binding with `[innerHTML]`.
- Cover image: optional, stored as a compressed base64 data URI on the post
  (resize client-side to ~1000px wide, JPEG ~70% quality before storing). This is
  a known V1 constraint — localStorage is capped around 5–10MB per origin — not a bug.

## What NOT to build
- No gamification, no badges, no rewards, no leaderboards.
- No notifications or reminders.
- No social features, no real auth, no multi-user support.
- No AI chat.
- No mascot or character — personality comes from color, shape, and icons.
- No loading spinners, no infinite scroll. No rich text editor — **except**
  the Blog create/edit page, which is a documented, explicit exception (see
  Blog module specifics above).

## V1 → V2 migration note
`StorageService` is the only intended swap point. In V2 it would call a FastAPI
backend instead of localStorage; everything above it (feature services, components)
should need zero changes. Keep all persistence behind services so this stays true.
