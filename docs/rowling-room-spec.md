# Thinkingify — Rowling Room (Writing Module) — Planning Notes

**Status:** Product direction agreed. Content + implementation not yet started
(as of the writing of this document — see `ui/CLAUDE.md` for what has since
shipped).

**Purpose:** Hand-off context for Claude Code before resuming development.

This document is a verbatim transcription of the original planning-notes PDF
shared by Nish. It is the ground-truth reference for the Rowling Room
feature; the implementation plan that built v1 of it is summarized in
`ui/CLAUDE.md`.

---

## 1. Origin & Philosophy

This module is inspired by a technique used with Neo (Nish's son) to teach
concepts like why Earth has seasons (aphelion/perihelion, axial tilt, tropic
of cancer/capricorn, etc.).

The technique has four stages:

1. **Deep input** — concept explained in detail, with diagrams and
   visualization.
2. **Active capture** — kid takes notes while listening/reading (can pause,
   scribble key points).
3. **Retrieval + reframe** — kid writes a blog explaining the concept in
   their own words, choosing a style (documentary / story / fun conversation
   between friends). This is not a summary — it's reconstruction, which is
   where real learning/memory embedding happens.
4. **Publish + share** — kid publishes the blog and can share it with
   friends (simple sharing, no complex social features). This creates a
   sense of accomplishment and ownership.

**Core belief driving product decisions:** writing opens up thinking. The
product should scaffold stages 2 and 3 (capture + reconstruction), not just
deliver content passively.

**Explicit anti-decision:** No YouTube / passive video. Conflicts with the
philosophy of active listening and note-taking. Audio (narrated by Nish, or
produced audio) + text + diagrams/images is the content format instead.

## 2. Product Structure

Thinkingify is organized into **Rooms** (subject/skill areas), each named
after a real or iconic figure to make it relatable and aspirational for
kids — not just a subject label.

Locked room names (v1):

| Room | Namesake | Notes |
|---|---|---|
| Writing | Rowling | Flagship room — this spec covers this room in detail |
| Maths | Ramanujan | Self-taught genius story, notebooks — very kid-grabbing if told well |
| Science | Einstein | Most universally kid-recognized choice |
| Puzzle | Sherlock Holmes | Fictional, but the strongest "puzzle solver" archetype for kids |

**Design intent:** each room can have a short "why this room is named after
them" blurb the kid reads once, rather than heavy branding throughout.

**Audience:** Designed for multiple kids, not just Neo — Neo is the first
user, but the product should not be hardcoded to a single user.

**Sharing:** Kept intentionally simple for v1 (e.g. shareable link), not a
social feed — consistent with the anti-addictive, non-engagement-maximizing
philosophy already established for Thinkingify.

## 3. Content Model — "Topic"

Each Topic (inside the Rowling Room, but structure should generalize to
other rooms later) needs:

- `title`
- `written_explainer` — chunked text, written in a teaching voice (not
  textbook style), broken into digestible sections
- `images/diagrams` — inline visual aids where the concept needs them (e.g.
  earth tilt, sun angles)
- `audio_explanation` — narrated audio walking through the concept (replaces
  video)
- ~~`youtube_links`~~ — explicitly dropped, do not build this

**Content creation process (for Nish, not engineering):** Nish gives a rough
dump of what he'd cover for a topic → Claude (chat) drafts a structured
explainer + flags where diagrams help, optionally a voiceover script → Nish
reviews/edits, sources or sketches diagrams, records audio. Target ~20-30
min/topic once rhythm is established. Start with 3-5 topics, not a full
curriculum, to validate the core loop first.

**Note:** Random/algorithmic topic selection was discussed and explicitly
parked — not v1. Revisit once 10-15 topics exist.

## 4. User Flow — Rowling Room

1. **Room landing** — short intro in Rowling's "voice," then a grid/list of
   Topic cards (title + small icon, minimal clutter).
2. **Topic page** — on selecting a topic, kid sees:
   - Written explainer (chunked)
   - Inline images/diagrams
   - Audio player (primary way to "hear" the explanation; text is
     backup/reference)
   - Notes panel (side panel, persistent, empty and ready to use)
3. **Active learning** — kid listens/reads, pauses anytime, takes notes in
   the side panel. Notes panel should NOT be a separate screen/context
   switch.
4. **Transition to writing** — CTA: "Ready to write your own take?" → kid
   picks a style:
   - Documentary style
   - Story style (e.g. friends talking about the topic)
   - Fun/casual style

   Present as simple cards with one-line descriptions, not a dropdown.
5. **Writing Studio** — writing canvas opens. Open design question
   (unresolved at spec time): should the Notes panel remain visible
   alongside the writing box on the same screen (Nish's likely preference,
   given the emphasis on "refer to notes while writing"), or should it be a
   separate step (finish notes → then move to distinct writing screen)?
   Recommendation (adopted): same screen, notes always visible during
   writing. Depending on chosen style, light scaffolding/prompts could be
   shown (e.g. documentary style might prompt "What's your opening fact?").
6. **Publish** — kid clicks "Publish to your blog" →
   confirmation/accomplishment moment → shareable link generated.

## 5. Open Questions / Not Yet Decided

*(as of spec time — resolutions reached during implementation planning are
noted inline)*

- Notes-panel-and-writing-studio: same screen vs. separate steps.
  **Resolved: same screen, notes always visible.**
- Exact data model for Topic, Note, and Blog/Post entities. **Resolved: see
  `ui/CLAUDE.md`'s Rooms IA section and the backend `Topic`/`Note`
  models/migrations.**
- Whether style selection affects stored structure of the post (e.g.
  structured prompts saved as metadata) or is purely a UI/writing-aid layer.
  **Resolved: UI/writing-aid layer only — `style` is stored as a plain
  string for the placeholder prompt, never as structured content metadata.**
- Audio production approach — self-recorded by Nish vs. AI-generated
  voiceover from a script Claude drafts. **Still open — a content workflow
  decision, not engineering.**
- How diagrams get created/sourced (hand-sketched, AI-generated, stock).
  **Still open — a content workflow decision, not engineering.**

## 6. Explicitly Parked (not v1)

- Random topic algorithm / recommender.
- YouTube or any video content.
- Complex social/sharing features (feeds, likes, comments) — deliberately
  excluded per anti-addictive philosophy.
- Puzzle, Maths (Ramanujan), Science (Einstein) rooms — naming locked,
  content/flow not yet designed (to be discussed in future sessions).
