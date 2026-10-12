import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.curriculum import AssetOut, ChapterOut, ConceptOut, ItemPublicOut, SubjectOut
from app.services import curriculum_service as svc

# Learner-facing reads. Every endpoint requires auth and returns only `live`
# content (items/assets) — non-live curriculum is never exposed here.
router = APIRouter(prefix="/curriculum", tags=["curriculum"])

Db = Annotated[AsyncSession, Depends(get_db)]
Learner = Annotated[User, Depends(get_current_user)]


@router.get("/subjects", response_model=list[SubjectOut])
async def list_subjects(db: Db, _: Learner):
    return await svc.list_subjects(db)


@router.get("/subjects/{subject_id}/chapters", response_model=list[ChapterOut])
async def list_chapters(subject_id: uuid.UUID, db: Db, _: Learner):
    return await svc.list_chapters(db, subject_id)


@router.get("/chapters/{chapter_id}/concepts", response_model=list[ConceptOut])
async def list_concepts(chapter_id: uuid.UUID, db: Db, _: Learner):
    return await svc.list_concepts(db, chapter_id)


@router.get("/concepts/{concept_id}/items", response_model=list[ItemPublicOut])
async def list_items(concept_id: uuid.UUID, db: Db, _: Learner):
    return await svc.list_live_items(db, concept_id)


@router.get("/concepts/{concept_id}/assets", response_model=list[AssetOut])
async def list_assets(concept_id: uuid.UUID, db: Db, _: Learner):
    return await svc.list_live_assets(db, concept_id)
