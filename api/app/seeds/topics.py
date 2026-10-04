"""Seed the curated Rowling Room topics (the proprietary learning content).

Idempotent (skips a topic whose slug already exists) and authored under the
dev-login user (creating it if absent). Run standalone:

    python -m app.seeds.topics

The topic rows live in `topics_data.json` (next to this file) and the
narration audio in `topic_audio/`. These were authored through the Studio UI
in the original Thinkingify Supabase project; when the app was folded into the
shared `thinkingify` schema the content was captured here so it is
version-controlled and reproducible rather than living only in one database.
The audio files are pushed to Storage separately by `upload_topic_audio.py`;
`audio_url` already points at the current project's public bucket.
"""

import asyncio
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.topic import Topic, TopicStatus
from app.models.user import User, UserRole
from app.services.auth_service import DEV_USER_EMAIL, DEV_USER_GOOGLE_SUB, DEV_USER_NAME

_DATA = Path(__file__).parent / "topics_data.json"


async def seed() -> None:
    topics = json.loads(_DATA.read_text())
    async with AsyncSessionLocal() as db:
        author = (
            await db.execute(select(User).where(User.google_sub == DEV_USER_GOOGLE_SUB))
        ).scalar_one_or_none()
        if author is None:
            author = User(
                id=uuid.uuid4(),
                google_sub=DEV_USER_GOOGLE_SUB,
                email=DEV_USER_EMAIL,
                name=DEV_USER_NAME,
                role=UserRole.learner,
            )
            db.add(author)
            await db.commit()
            await db.refresh(author)

        created = 0
        for t in topics:
            exists = (
                await db.execute(select(Topic.id).where(Topic.slug == t["slug"]))
            ).scalar_one_or_none()
            if exists is not None:
                continue
            status = TopicStatus(t["status"])
            db.add(
                Topic(
                    id=uuid.uuid4(),
                    title=t["title"],
                    slug=t["slug"],
                    explainer_markdown=t["explainer_markdown"],
                    audio_url=t["audio_url"],
                    audio_transcript=t["audio_transcript"],
                    themes=t["themes"],
                    status=status,
                    order_index=t["order_index"],
                    author_id=author.id,
                    published_at=datetime.now(UTC) if status == TopicStatus.published else None,
                )
            )
            created += 1
        await db.commit()
        print(f"Seeded {created} new topic(s) ({len(topics) - created} already present).")


if __name__ == "__main__":
    asyncio.run(seed())
