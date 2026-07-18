import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.models.user import User


async def get_or_create(db: AsyncSession, user: User, topic_id: uuid.UUID) -> Note:
    result = await db.execute(select(Note).where(Note.user_id == user.id, Note.topic_id == topic_id))
    note = result.scalar_one_or_none()
    if note is None:
        note = Note(id=uuid.uuid4(), user_id=user.id, topic_id=topic_id)
        db.add(note)
        await db.commit()
        await db.refresh(note)
    return note


async def update(db: AsyncSession, note: Note, body: str) -> Note:
    note.body = body
    await db.commit()
    await db.refresh(note)
    return note
