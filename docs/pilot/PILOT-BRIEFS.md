# Thinkingify Class 4 Pilot: Claude Code briefs

Put this file at `docs/pilot/PILOT-BRIEFS.md` in the repo (and the spec doc's export next to it as `docs/pilot/SPEC.md`). Work one phase at a time. Each phase is its own branch and PR (`feature/pilot-phase-N-...`), merged before the next starts.

## Read first (applies to every phase)

1. Read `ui/CLAUDE.md`, `api/README.md`, `api/docs/schema-migration-runbook.md` and `docs/rowling-room-spec.md`. Follow the existing conventions: Angular 20 standalone components with signals and lazy `loadComponent` routes; FastAPI `router -> service -> model` layering; Alembic migrations in the `thinkingify` schema; tests in `api/tests/`.
2. **Principles that must hold everywhere:** no leaderboards, no streaks, no points or ranks, no countdown pressure, non-punitive feedback, parent-facing reporting. If a task seems to need one of these, stop and ask.
3. **Content rule:** textbook scans and olympiad question banks are private reference only. Never commit them, never put their text in a prompt, never show them to users. Generated content comes from our own concept map and must pass the dedupe check (Phase 2).
4. **Child safety:** nothing generated reaches a child until a person marks it `live`. Every live model call goes through the safety filter and daily caps (Phase 7). Until Phase 7 exists, keep live AI features behind a flag.
5. **Scope discipline:** the pilot is Class 4 CBSE Maths and EVS only. Do not build other classes, payments, ranks or social features.
6. Definition of done for every phase: `npm run build` (both configs) and `ng test` pass, `pytest` passes, new code has tests, no console errors, and `ui/CLAUDE.md` gets a short dated section describing what changed.

Add this block to `ui/CLAUDE.md` before starting:

```
## Class 4 pilot (started 2026-10-10)
Direction: CBSE Class 4 Maths + EVS, original concept map, olympiad-style "Crack it" track, parent-first onboarding.
Spec and phase briefs: docs/pilot/SPEC.md and docs/pilot/PILOT-BRIEFS.md. Private reference material is never committed or sent to models.
```

---

## Phase 0: Tidy and new look (start here)

**Goal:** the app looks and feels like the new design on a tablet, and shows only what is finished. No new backend.

### 0.1 Hide unfinished areas behind a pilot flag
- Add `pilotMode: true` to `environment.ts` and `environment.prod.ts` (and a tiny `FeatureFlagService`, so it can be read in components and guards).
- With `pilotMode` on:
  - Remove **Einstein** and **Progress** from `NAV_ITEMS` in `layout/nav/nav.component.ts` (the mobile bottom tab bar is driven by the same array; update the "fixed at 6 tabs" comment, it becomes 4 tabs: Home, Ramanujan, Rowling, Sherlock Holmes).
  - Redirect `/einstein` and `/progress` to `/dashboard`.
  - Keep `/studio/**` working for admins, but remove any Studio link from the learner nav and the learner dashboard.
- Leave all code in place; only routing and nav change. Flag off must restore today's behavior.

### 0.2 Design tokens
Update `ui/tailwind.config.js` and `src/styles.css` to the new look. Keep existing token names so the 80-odd components do not need touching; change values and add new tokens.

| Token | Old | New | Use |
| --- | --- | --- | --- |
| `ink` | #1C1917 | #16213B | text, dark cards |
| `paper` | #FAFAF7 | #EDF1F5 | page ground |
| `cloud` | #F0EFE9 | #D5DCE6 | borders, dividers (add a lighter `cloud-soft` #E3E8EF for bars) |
| `moss` | #4A7C59 | #14746F | primary interactive color (still the only color on clickable elements, per existing rule) |
| `moss-dark` | #2E5238 | #0E5652 | hover |
| `muted` | #78716C | #56627A | secondary text |
| `navy` | #33415C | #16213B | dark surfaces |
| `amber` | #D97706 | #F5C26B | "Crack it" accent on dark surfaces |

Add room tones: `room-ramanujan` #14746F (tint #DDF1EE), `room-einstein` #2F5DA8 (tint #E1EBF9), `room-rowling` #7B3F86 (tint #F0E3F3), `room-sherlock` #A8650F (tint #FBEBD0). All text-on-color pairs must meet WCAG AA (4.5:1; 3:1 for 24px+); check them.

Fonts: replace Fraunces with **Bricolage Grotesque** (600, 700) for `font-display`; keep DM Sans. Update the Google Fonts link in `src/index.html`. Set `border-radius` defaults to larger, friendlier corners (cards 20-24px, buttons 12-14px); the current `sm: 2px` override goes away.

### 0.3 Shell and tablet pass
- Target viewports: 1180x820 and 820x1180 (tablets), 390x844 (phone), 1440x900 (desktop). Touch targets at least 44px; base text 16px or more; one primary action per screen.
- Keep the collapsible sidebar on wide screens; on tablet portrait and phone use the bottom bar.

### 0.4 New child home at `/dashboard`
Replace the content of `features/dashboard/dashboard.component.ts` (keep the route and guard behavior):
- Header: wordmark left, child chip (initial avatar + name + "Class 4") right.
- Greeting: "Hi {name}. Ready to think?"
- Row 1: **Today's chapter card** (flex 1.7) and **Crack it card** (flex 1, dark `ink` surface, amber label).
  - Chapter card: label "TODAY'S CHAPTER", title, one line of status, a 5-step **trail** (done = filled `moss` circle with check; current = ringed circle; upcoming = dashed circle), primary button "Continue: ...", secondary button.
  - Crack it card: "One puzzle", the prompt, "No timer. No rank. Tell us how you know.", a "Try it" button.
  - Until the concept map exists (Phase 1+), feed both from a small `HomeService.getContinue()` that returns `{ room, title, subtitle, steps[], route }` chosen from the learner's latest existing activity (in-progress writing in Rowling, current Brothers tier, latest Kakooma operation). Define the return type now so Phase 3 can swap the source without UI changes. Crack it shows the next Kakooma puzzle for now.
- Row 2: **Rooms** as four cards in a grid with a 6px colored top border: room name (display font), subject label in the room color, one line of what is inside. Only show doors that exist.
- No points, streak counters, badges or comparisons anywhere on this screen.

### 0.5 Reusable room shell
Create `shared/components/room-shell/room-shell.component.ts`:
- Inputs: `roomName`, `subjectLabel`, `tone` (ramanujan | einstein | rowling | sherlock), `doors: { id, title, blurb, status, route, icon }[]`, and a projected sidebar slot for a chapter list.
- Layout: left column with title and chapter list; right column with the doors (3-column grid) and a "how it works" strip slot. The recommended door gets a ringed border.
- Apply it to **Ramanujan** (`features/ramanujan/ramanujan.component.ts`): doors for the current coached problem solving ("Learn" for now) and the Brothers warm-up. Do not render "Write it down" or "Crack it" doors until they work.
- Apply it to **Rowling** and **Sherlock** where it fits without rewriting their flows; if it does not fit cleanly, restyle only.

### 0.6 Landing page for parents at `/`
Restyle `features/vision/vision.component.ts` into the parent landing page, using the existing section components where they still fit:
- Hero: label "CBSE CLASS 4 · MATHS & EVS · OLYMPIAD THINKING", headline "Prepare for CBSE. Think like an olympiad champion.", sub-line "Thinkingify helps your child understand each chapter, explain it in their own words, and take on olympiad-style puzzles, so they learn to crack the hard questions themselves.", primary CTA "Join the Class 4 pilot".
- Dark band "How a concept sticks": Listen, Write, Solve, Recall.
- Three value cards (CBSE chapters; olympiad-style thinking; a weekly report that tells you something).
- "Our promises" list: no leaderboards, ranks or streaks; no ads or selling data; mistakes are investigation, not penalty; parents consent first and can see and delete everything.
- Pilot section and CTA. The CTA goes to the existing sign-in for now; Phase 6 replaces it with parent-first sign-up.
- Do not claim outcomes ("guaranteed", "rank", "toppers"). Keep copy as written.

### 0.7 Tests and checks
- Component tests for `FeatureFlagService`, nav filtering under `pilotMode`, `HomeService.getContinue()` selection, and `RoomShell` rendering only available doors.
- Take screenshots at the four viewports for home, Ramanujan, landing, and the Rowling writing studio; put them in the PR description.

**Acceptance:** with `pilotMode` on, a learner sees only Home, Ramanujan, Rowling, Sherlock; the new look is applied app-wide with no broken screens; flag off restores the old nav; builds and tests pass; no leaderboards, streaks or scores introduced.

---

## Phase 1: Concept map (backend and admin)

**Goal:** the data model and admin screens for chapters, concepts, skills, assets, items and book maps. No generated content yet.

- Alembic migrations (next number after `0020`) and SQLAlchemy models for `subject`, `chapter`, `concept` (with prerequisite links), `skill`, `asset`, `item`, `book_map`, `mastery`, `writing` as described in the spec's concept-map table. Item `status`: `draft | reviewed | live | retired`.
- `/api/v1/curriculum/*` read endpoints for learners (only `live` items and assets), and `/api/v1/admin/curriculum/*` write endpoints behind the existing admin guard.
- Admin screens under `/studio/curriculum`: tree of chapters and concepts, item list with filters (status, concept, skill, kind), an item detail with accept / edit / retire, and a review queue of `draft` items.
- Seed one Class 4 Maths chapter ("Big Numbers" placeholder) and one EVS chapter with concepts only (no items) to prove the shape.
- Tests: schema constraints, status transitions (illegal transitions 409), learners never see non-live content, prerequisite cycles rejected.

**Acceptance:** admin can create and edit the full tree; learner endpoints return nothing that is not `live`.

## Phase 2: Content pipeline (offline)

**Goal:** generate, dedupe and review items and audio scripts for one Maths and one EVS chapter.

- A CLI under `api/app/pipeline/` (not served by the API): `ingest` (private reference intake: OCR of local scans into a local-only folder that is gitignored; extract concepts and question patterns into proposed concept-map entries for human approval), `generate`, `dedupe`, `export-review`.
- `generate` prompts only from the concept description, difficulty band and item kind. **Maths items:** numbers and answers computed in code; the model writes wording and context only. **EVS items and audio scripts:** model-written, age-appropriate, Indian context.
- `dedupe`: embed generated items and the private reference set (kept local); drop items above a similarity threshold; write the score to the item.
- Output lands in `item`/`asset` as `draft`. Text-to-speech runs only from reviewed scripts and stores audio in the existing Supabase storage bucket (reuse `upload_topic_audio.py` patterns).
- Add `.gitignore` entries for the reference folder; add a test that fails if any file under the reference path is tracked.
- Tests: answer computation correctness for maths templates, dedupe threshold behavior, no reference text in assembled prompts.

**Acceptance:** one Maths and one EVS chapter produce drafts you can review in the Phase 1 admin; nothing is `live` without a human accept.

## Phase 3: Learn and practice

**Goal:** the Learn door for Ramanujan and Einstein using live content.

- Learner flow: chapter trail -> concept -> question-first walkthrough (ask, let the child answer or say "not sure", then reveal a short explanation or visual) -> apply-items.
- Mastery per concept against the child's own baseline, reusing the logic in `brother_service.py` (median of first N attempts as baseline, mastery at a fraction of baseline with an accuracy floor). Add retention/demotion for Brothers here since it shares the logic. Demotion never re-locks anything already unlocked.
- Replace `HomeService.getContinue()`'s stub source with real concept progress.
- Turn on the Einstein room and nav entry (remove its `pilotMode` hide) once its Learn door has live content.
- Tests: baseline and mastery transitions, prerequisite gating, nothing punitive on wrong answers.

## Phase 4: Write it down

**Goal:** listen -> write -> solve -> recall for a concept.

- Audio player step with transcript hidden until after writing (reuse `audio-player` and the Rowling editor and sketch components).
- Understanding-focused guide: extend `companion_service.py` with a `concept` mode. Same four-level nudge ladder, but nudges target gaps in the child's explanation against the concept's key ideas ("what happens to the water after it evaporates?"). Never give the answer; never write for the child. Add the fact-leak guard patterns already used in `fact_leak_guard.py`.
- Store `writing` rows (explain, recall). Recall is scheduled two days after a good explanation; a concept becomes `held` after a good recall.
- Gate live guide calls behind the Phase 7 caps; until then behind a flag.
- Tests: ladder escalation, no direct answers in guide output (use the fact-leak guard tests as a model), recall scheduling.

## Phase 5: Crack it

**Goal:** skill-tagged olympiad-style puzzles.

- Serve `item` rows of kind `puzzle` by skill and level; no timer, no rank. Wrong answer opens an "investigate" step (as in Ramanujan error discovery) before any reveal; the child can request a nudge instead.
- After each puzzle the child writes one line: "how I knew". Store it in `writing`.
- Reuse Kakooma engine pieces where they fit; do not remove Kakooma.
- Skill progress is "readiness by skill" shown against the child's own history only.

## Phase 6: Parent space

**Goal:** parent-first sign-up and the weekly report.

- Parent signs in with Google, reads a plain-language privacy page and gives explicit consent before any child profile can exist. Store consent with timestamp and version.
- Child profiles (name, class, avatar) with picture-and-PIN login on the family device; children never need an email. Rework the auth flow and `family` models accordingly; keep guardian approval for publishing.
- Chapter and exam-date picker (book map -> chapters in the exam) drives the order of chapters on home.
- Weekly report: extend `parent_report_service.py` with maths and EVS concept states (solid / needs another look / not started), Crack it readiness by skill, one writing excerpt, one dinner-table conversation prompt. Delivered as a page and an email.
- Settings: export and delete a child's data.
- Replace the landing CTA with the parent sign-up.

## Phase 7: Pilot ready

**Goal:** safe, affordable and reliable enough for other families.

- Daily caps per child on guide and coach messages (config), with a gentle message when reached.
- Input and output safety filter around every model call; block and log.
- Conversation log visible to the parent for their child.
- "Send feedback" and "Report a question" buttons; reports return items to `draft`.
- Basic privacy-safe usage events (sessions per week, rooms used, completion).
- Move the API off the Render free tier (or to the Oracle VM); error tracking; nightly database backups.
- Fallbacks: if the model is down or capped, learners still get reviewed items and audio.

---

## How to run this with Claude Code

Start each phase with: "Read docs/pilot/PILOT-BRIEFS.md and ui/CLAUDE.md. Do Phase N only. Make a plan first, list any questions, then implement on a branch."
