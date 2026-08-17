from datetime import date

from app.models.content import ContentStatus
from app.services import content_service, diary_service


async def test_get_or_create_today_creates_a_private_draft(db, learner_user):
    day = date(2026, 8, 17)
    entry = await diary_service.get_or_create_today(db, learner_user, day)
    assert entry.style == "diary_entry"
    assert entry.topic_id is None
    assert entry.entry_date == day
    assert entry.diary_theme == diary_service.DEFAULT_DIARY_THEME
    assert entry.status == ContentStatus.draft
    assert entry.author_id == learner_user.id


async def test_get_or_create_today_is_one_per_day(db, learner_user):
    day = date(2026, 8, 17)
    first = await diary_service.get_or_create_today(db, learner_user, day)
    second = await diary_service.get_or_create_today(db, learner_user, day)
    assert second.id == first.id

    other_day = await diary_service.get_or_create_today(db, learner_user, date(2026, 8, 18))
    assert other_day.id != first.id


async def test_get_or_create_today_is_scoped_per_user(db, learner_user, author_user):
    day = date(2026, 8, 17)
    mine = await diary_service.get_or_create_today(db, learner_user, day)
    theirs = await diary_service.get_or_create_today(db, author_user, day)
    assert mine.id != theirs.id


async def test_list_entries_newest_first_and_scoped(db, learner_user, author_user):
    await diary_service.get_or_create_today(db, learner_user, date(2026, 8, 15))
    await diary_service.get_or_create_today(db, learner_user, date(2026, 8, 17))
    await diary_service.get_or_create_today(db, learner_user, date(2026, 8, 16))
    await diary_service.get_or_create_today(db, author_user, date(2026, 8, 17))

    entries = await diary_service.list_entries(db, learner_user)
    assert [e.entry_date for e in entries] == [date(2026, 8, 17), date(2026, 8, 16), date(2026, 8, 15)]


async def test_diary_entry_stays_private_until_published(db, learner_user):
    entry = await diary_service.get_or_create_today(db, learner_user, date(2026, 8, 17))
    published = await content_service.list_published(db)
    assert entry.id not in {c.id for c in published}

    # Opt-in publish makes it public, like any other content.
    await content_service.transition(db, entry, "self_publish")
    published = await content_service.list_published(db)
    assert entry.id in {c.id for c in published}


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


def test_diary_endpoints_round_trip(client, learner_user):
    token = _token_for(learner_user, "learner")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/v1/diary/today", json={"entry_date": "2026-08-17"}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["entry_date"] == "2026-08-17"
    assert body["style"] == "diary_entry"
    entry_id = body["id"]

    # Same day → same entry.
    resp2 = client.post("/api/v1/diary/today", json={"entry_date": "2026-08-17"}, headers=headers)
    assert resp2.json()["id"] == entry_id

    entries = client.get("/api/v1/diary/entries", headers=headers)
    assert entries.status_code == 200
    assert len(entries.json()) == 1
