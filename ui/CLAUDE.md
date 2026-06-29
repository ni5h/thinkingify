# Thinkingify — Claude Code Context

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
- Placeholder components for all six features (just a heading + "Phase N
  builds this here" — not real implementations yet)

Not started yet — next up is **Phase 2: Home Dashboard**
(`features/home/home.component.ts`: greeting, streak badge, today's
puzzle/lesson quick-action cards, journal preview), then Phases 3–6 (Puzzle,
Learn, Journal, Progress) per the module descriptions below, then the Blog
module. `assets/data/puzzles.json` and `assets/data/lessons.json` have not
been created/seeded yet.

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
3. No shadows. No rounded card corners (buttons max 2px radius). No modals.
   No loading spinners (data is local — if something needs a spinner, reconsider
   the architecture). No looping/bouncing animations. No emojis in UI chrome.
4. Buttons use a left border accent (`border-l-4 border-moss-dark` etc.), not
   rounded pills — see button variants below.
5. The only animation is `slideUp` on page entry (translateY 8px→0, opacity 0→1, 300ms ease-out).
6. The Journal module is the most important screen in the app — it must feel like
   a notebook page, not a form: generous line-height, minimal chrome, plain textareas.

### Button variants
- Primary: `bg-moss text-white border-l-4 border-moss-dark`
- Secondary: `bg-transparent border border-cloud border-l-4 border-ink`
- Ghost: `text-muted border-l-4 border-transparent`, hover shows moss border

### Cards
White background, `border border-cloud`, no shadow, no border-radius.

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
- `/blog/manage/new`, `/blog/manage/:id/edit` — plain markdown textarea + a
  "Preview" toggle button (same pattern as Puzzle's "Show Hint"). No rich-text
  toolbar. Render markdown with `marked`, and sanitize the rendered HTML before
  binding with `[innerHTML]`.
- Cover image: optional, stored as a compressed base64 data URI on the post
  (resize client-side to ~1000px wide, JPEG ~70% quality before storing). This is
  a known V1 constraint — localStorage is capped around 5–10MB per origin — not a bug.

## What NOT to build
- No gamification, no badges, no rewards, no leaderboards.
- No notifications or reminders.
- No social features, no real auth, no multi-user support.
- No AI chat.
- No loading spinners, no rich text editor, no infinite scroll.

## V1 → V2 migration note
`StorageService` is the only intended swap point. In V2 it would call a FastAPI
backend instead of localStorage; everything above it (feature services, components)
should need zero changes. Keep all persistence behind services so this stays true.
