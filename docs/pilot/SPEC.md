# Thinkingify Class 4 Pilot Spec

Date: 2026-10-10

Thinkingify's pilot teaches CBSE Class 4 Maths and EVS through an original concept map, with olympiad-style challenges that grow the same thinking.

## Scope

The pilot covers CBSE Class 4 Maths and EVS, with one olympiad-style track per subject, for 5-8 families around Neo's friend circle.

- **In:** parent-first sign-up, child profiles, an original concept map for Class 4 Maths and EVS, Learn / Write it down / Crack it in each subject room, a weekly parent report.
- **Kept from today:** Rowling Room, Brothers fluency, Kakooma, Google login, family linking.
- **Hidden for the pilot:** the Studio/blog CMS, old localStorage-only modules, any room without content.
- **Out:** other classes and subjects, ranks, streaks, leaderboards, timers that pressure, payments.
- **Content rule:** the scanned textbooks and olympiad banks are private reference only. They are never shown to users, never stored in the repo, and never pasted into generation prompts.

## Product structure

The four rooms stay; the two subject rooms each get three doors, so olympiad sits inside the subject rather than beside it.

| Room | Subject | Doors | Pilot status |
| --- | --- | --- | --- |
| Ramanujan | Maths, Class 4 CBSE | Learn, Write it down, Crack it, plus the Brothers warm-up | Build |
| Einstein | Science and EVS, Class 4 CBSE | Learn, Write it down, Crack it | Build (today a placeholder) |
| Rowling | Writing | Styles, companion, diary, posts; also powers Write it down | Keep, extend |
| Sherlock | Puzzles and reasoning | Kakooma as warm-up; feeds Crack it skills | Keep |

Home is organised around **today's chapter** with one Continue button, then the rooms as doors. Progress is a trail of concepts lighting up. No points, streaks or ranks anywhere.

Parents get a separate space: sign-up and consent, child profiles, the chapter and exam-date picker, and the weekly report.

## Concept map and skill taxonomy

Everything the child sees hangs off one original concept map, so content, mastery and reports share the same ids. A concept is an idea ("carrying in addition"); a skill is a reasoning habit ("working backwards").

| Entity | Key fields | Notes |
| --- | --- | --- |
| subject | id, name (maths, evs), class | Class 4 only for the pilot |
| chapter | id, subject, title, order, book_refs | Our own title; book_refs map to the child's textbook chapters |
| concept | id, chapter, title, order, prerequisites[] | The unit of learning and mastery |
| skill | id, subject, name, level (1-4) | Olympiad habits, shared across chapters |
| asset | id, concept, kind (audio, script, visual), status | Audio scripts are written by us from the concept, not from the book |
| item | id, concept, skill?, kind, difficulty, body, answer_key, status | kind: recall, apply, explain, spot-the-mistake, puzzle; status: draft, reviewed, live, retired |
| book_map | book, chapter_ref, concept_ids[] | Metadata only: lets a parent pick their child's book and chapters |
| mastery | child, concept, baseline, state | Measured against the child's own baseline, as in Brothers |
| writing | child, concept, kind (explain, recall), text, feedback | Powers the parent report and the recall step |

Two tracks use the same item table: **Learn** items carry a concept, **Crack it** items carry a skill and a concept. A concept is *understood* once the child has explained it in writing and answered apply-items correctly at their own baseline speed, then holds it at recall.

## Content pipeline

Content is generated once, offline, reviewed by a person, and only then served. Live AI is reserved for the Socratic guide.

1. **Reference intake (private).** Scan the textbooks and olympiad banks into a private bucket. OCR them and extract only *concepts, learning outcomes and question patterns* into the concept map. The scans and extracted text are never shown to users and never placed in a generation prompt.
2. **Generate from the taxonomy.** For each concept and skill, prompt from our own concept description, difficulty band and item kind. Maths items get numbers and answers computed in code; the model writes only the wording and context. EVS items and audio scripts are model-written in our own words, pitched at a nine-year-old with Indian context.
3. **Dedupe against the sources.** Embed every generated item and compare it with the private reference set. Anything above a similarity threshold, or flagged on a manual look, is dropped. Log the score with the item.
4. **Review.** A person reads every item for correctness, age fit and a single valid answer, then marks it live. For the pilot, that is Nish or a teacher friend, one chapter per sitting.
5. **Serve and monitor.** Items go live with a "report this question" button. Reports pull an item back to draft.

Audio is produced by text-to-speech from the reviewed script, so a script change regenerates the audio.

## The three flows

Each concept has the same shape, so a child always knows what to do next. Sessions target about 15 minutes.

**Learn** is question-first. The guide asks, the child answers or says "not sure", and only then does a short explanation or visual appear. Maths concepts that are procedures (carrying, borrowing) always pair the explanation with a visual or manipulative.

**Write it down** reuses the Rowling engine:

1. **Listen.** One 2-4 minute audio on one concept. The transcript is hidden until after the writing step, and can be opened on request.
2. **Write.** The child explains the idea to a friend. Typing, voice input and the existing sketch tool are all allowed. The guide runs the four-level nudge ladder, but on *understanding* ("what happens to the water after it evaporates?"), not just spelling and grammar.
3. **Solve.** Three to five apply-items on the same concept.
4. **Recall.** Two days later, a short write-from-memory prompt. The concept is *held* only after a good recall.

**Crack it** serves puzzle items by skill and level. No timer, no rank. A wrong answer opens an "investigate" step (as in Ramanujan's error discovery), and the child can always ask for a nudge instead of the answer. After each puzzle the child writes one line: "how I knew".

The design principles apply to all three: no streaks, no leaderboards, non-punitive feedback, parent-facing reporting.

## Parent experience

Parents sign up and consent first; the child never needs an email address.

- **Sign-up and consent.** The parent signs in with Google, reads a plain-language privacy page (what is stored, what goes to the AI, how to delete), and gives explicit consent before any child profile exists. This is how the pilot meets India's DPDP Act expectation of verifiable parental consent for under-18s.
- **Child profiles.** The parent adds a child (name, class, avatar). The child signs in with a picture or PIN on the family's device.
- **Plan for the exam.** The parent picks the textbook and the chapters in the exam, and optionally an exam date. The home screen then orders chapters accordingly.
- **Weekly report.** Per concept: solid, needs another look, or not started. Olympiad readiness by skill, shown against the child's own past, never a rank. One excerpt the child wrote, and one conversation prompt for dinner.
- **Feedback and control.** A "send feedback" button, a "report a question" button, and delete-my-child's-data in settings.

The existing family-linking flow (request, accept, guardian approval) is reused for guardians who are not the account owner.

## AI safety, cost and quality

- **Daily caps per child** on guide and coach messages, set in config, with a gentle "that's enough thinking for today" message when reached.
- **Input and output filter** around every model call (age-appropriate language, no personal data requests, no off-topic drift). Block and log rather than answer.
- **Conversation log** visible to the parent for their child, and to us for quality review.
- **Model choice.** Haiku with prompt caching for the guide and coach; larger models only offline for content generation. Do not send children's writing to services that train on it (the Gemini free-tier caveat stays).
- **Fallbacks.** If the model is down or the cap is hit, the child still gets the reviewed items and audio; only the live guide pauses.
- **Quality gate.** Nothing generated reaches a child until a person marks it live. "Report this question" returns an item to draft.
- **Reliability.** Move off the Render free tier, which cold-starts, to an always-on host; add error tracking and nightly database backups.

## Build plan

Phases are ordered so the first one is shippable to Neo alone, and the third is shippable to friends. The detailed briefs are in `PILOT-BRIEFS.md`.

| Phase | What ships | Main work in the repo |
| --- | --- | --- |
| 0. Tidy | Hide unfinished rooms and modules, new look shell, tablet pass | Routing and nav in `ui/`, feature flags, new home and room layouts |
| 1. Concept map | Schema and admin screens to manage concepts, items, assets and book maps | New Alembic migrations, models and services in `api/`, a review screen in the Studio area |
| 2. Pipeline | Offline generation, dedupe and review for one Maths and one EVS chapter | Scripts under `api/app/seeds/` or a new `pipeline/` folder, embeddings table, private storage bucket |
| 3. Learn and Practice | Concept pages, question-first walkthrough, items, mastery against baseline | Reuse Brothers mastery logic; new learn components in Ramanujan and Einstein |
| 4. Write it down | Audio, writing step, understanding-focused guide, solve, recall | Extend the companion service with a concept mode; reuse the Rowling editor and sketch component |
| 5. Crack it | Skill-tagged puzzle items, investigate step, "how I knew" line | Reuse Kakooma and puzzle services where they fit |
| 6. Parent space | Parent-first sign-up, consent, child profiles with PIN login, chapter picker, weekly report | Auth and family changes, extend `parent_report_service`, report email or page |
| 7. Pilot ready | Caps, filters, logging, feedback and report buttons, always-on hosting, backups, error tracking | Config, deploy, monitoring |

Phase 2 is the one to do by hand first: run one Maths chapter and one EVS chapter end to end, test with Neo, and fix the format before scaling to all chapters.

## Pilot success measures

Run 5-8 families for four weeks, with a 15-minute call with each parent in week 1 and week 4.

| Question | Signal | Healthy result |
| --- | --- | --- |
| Do children come back unprompted? | Sessions per child per week, started without a parent reminder (ask in the call) | Steady weekly return; daily use is not the goal |
| Do they finish what they start? | Share of Learn and Write it down sessions completed | Most sessions finished in about 15 minutes |
| Does writing help? | Recall quality two days after Write it down, versus apply-items alone | Recall is good for most held concepts |
| Do parents find the report useful? | Parent answer: "did it tell you something new?" | Most parents say yes in week 4 |
| Is the content right? | "Report this question" count per 100 items served | Low and falling; every report reviewed within a day |
| Would parents recommend it? | Parent answer in the week-4 call | Would pass it to another parent |

## Open questions

- [ ] Which Class 4 Maths and EVS books do the pilot families actually use, so the book map covers them?
- [ ] Who reviews EVS content for facts and Indian context: Nish, or a teacher friend?
- [ ] Text-to-speech voice for the audio: which service, and is an Indian-English voice available at acceptable cost?
- [ ] Child login on shared family tablets: picture-and-PIN, or a QR handoff from the parent's phone?
- [ ] Hosting: move the API to the Oracle VM, or a paid always-on tier on Render?
- [ ] Pilot timing: should it line up with the next school exam cycle, and what is the date?
- [ ] Olympiad scope: Maths reasoning only for the first cut, or Science too?
