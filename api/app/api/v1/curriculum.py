import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.curriculum import (
    AnswerIn,
    AnswerOut,
    AssetOut,
    ChapterOut,
    CheckSessionOut,
    CheckStartIn,
    ConceptOut,
    ConceptProgressOut,
    ItemPublicOut,
    SubjectOut,
)
from app.services import adaptive_service, concept_mastery_service, curriculum_service as svc

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


@router.get("/chapters/{chapter_id}/progress", response_model=list[ConceptProgressOut])
async def chapter_progress(chapter_id: uuid.UUID, db: Db, learner: Learner):
    concepts = await svc.list_concepts(db, chapter_id)
    return await concept_mastery_service.concept_progress(db, learner.id, concepts)


@router.post("/concepts/{concept_id}/check/start", response_model=CheckSessionOut)
async def start_check(concept_id: uuid.UUID, payload: CheckStartIn, db: Db, learner: Learner):
    session, item = await adaptive_service.start(
        db, learner, concept_id, think_results=payload.think_results, mode=payload.mode
    )
    return CheckSessionOut(
        session_id=session.id, index=1, total=session.total, item=ItemPublicOut.model_validate(item)
    )


@router.post("/check/{session_id}/answer", response_model=AnswerOut)
async def answer_check(session_id: uuid.UUID, payload: AnswerIn, db: Db, learner: Learner):
    session = await adaptive_service.get_session(db, learner, session_id)
    out = await adaptive_service.answer(
        db,
        learner,
        session,
        item_id=payload.item_id,
        choice=payload.choice,
        unsure=payload.unsure,
        hint_used=payload.hint_used,
        ms=payload.ms,
    )
    next_item = out.pop("next_item")
    return AnswerOut(
        **out, next_item=ItemPublicOut.model_validate(next_item) if next_item is not None else None
    )
