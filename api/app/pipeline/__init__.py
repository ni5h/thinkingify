"""Offline content pipeline for the Class 4 pilot (Phase 2).

Never imported by the served API — these are CLI-invoked scripts that generate,
dedupe and stage curriculum content as `draft` for human review. Content rules
(see docs/pilot/PILOT-BRIEFS.md "Read first"): the private reference set is
never committed, shown to users, or placed in a model prompt.
"""
