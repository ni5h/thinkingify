import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.curriculum import CurriculumStatus, ItemKind
from app.schemas.curriculum import (
    AssetCreate,
    AssetOut,
    AssetUpdate,
    BookMapCreate,
    BookMapOut,
    ChapterCreate,
    ChapterOut,
    ChapterUpdate,
    ConceptCreate,
    ConceptOut,
    ConceptUpdate,
    ItemCreate,
    ItemOut,
    ItemUpdate,
    SkillCreate,
    SkillOut,
    SkillUpdate,
    SubjectCreate,
    SubjectOut,
    SubjectUpdate,
)
from app.services import curriculum_service as svc

# Every route is admin-gated — curriculum is proprietary platform content.
router = APIRouter(
    prefix="/admin/curriculum",
    tags=["admin-curriculum"],
    dependencies=[Depends(require_admin)],
)

Db = Annotated[AsyncSession, Depends(get_db)]


async def _or_404(obj, what: str):
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found.")
    return obj


# --- Subjects ---
@router.post("/subjects", response_model=SubjectOut, status_code=201)
async def create_subject(body: SubjectCreate, db: Db):
    return await svc.create_subject(db, body)


@router.get("/subjects", response_model=list[SubjectOut])
async def list_subjects(db: Db):
    return await svc.list_subjects(db)


@router.patch("/subjects/{subject_id}", response_model=SubjectOut)
async def update_subject(subject_id: uuid.UUID, body: SubjectUpdate, db: Db):
    subject = await _or_404(await svc.get_subject(db, subject_id), "Subject")
    return await svc.update_subject(db, subject, body)


# --- Chapters ---
@router.post("/chapters", response_model=ChapterOut, status_code=201)
async def create_chapter(body: ChapterCreate, db: Db):
    return await svc.create_chapter(db, body)


@router.get("/chapters", response_model=list[ChapterOut])
async def list_chapters(db: Db, subject_id: uuid.UUID | None = None):
    return await svc.list_chapters(db, subject_id)


@router.patch("/chapters/{chapter_id}", response_model=ChapterOut)
async def update_chapter(chapter_id: uuid.UUID, body: ChapterUpdate, db: Db):
    chapter = await _or_404(await svc.get_chapter(db, chapter_id), "Chapter")
    return await svc.update_chapter(db, chapter, body)


# --- Concepts ---
@router.post("/concepts", response_model=ConceptOut, status_code=201)
async def create_concept(body: ConceptCreate, db: Db):
    return await svc.create_concept(db, body)


@router.get("/concepts", response_model=list[ConceptOut])
async def list_concepts(db: Db, chapter_id: uuid.UUID | None = None):
    return await svc.list_concepts(db, chapter_id)


@router.patch("/concepts/{concept_id}", response_model=ConceptOut)
async def update_concept(concept_id: uuid.UUID, body: ConceptUpdate, db: Db):
    concept = await _or_404(await svc.get_concept(db, concept_id), "Concept")
    return await svc.update_concept(db, concept, body)


# --- Skills ---
@router.post("/skills", response_model=SkillOut, status_code=201)
async def create_skill(body: SkillCreate, db: Db):
    return await svc.create_skill(db, body)


@router.get("/skills", response_model=list[SkillOut])
async def list_skills(db: Db, subject_id: uuid.UUID | None = None):
    return await svc.list_skills(db, subject_id)


@router.patch("/skills/{skill_id}", response_model=SkillOut)
async def update_skill(skill_id: uuid.UUID, body: SkillUpdate, db: Db):
    skill = await _or_404(await svc.get_skill(db, skill_id), "Skill")
    return await svc.update_skill(db, skill, body)


# --- Assets ---
@router.post("/assets", response_model=AssetOut, status_code=201)
async def create_asset(body: AssetCreate, db: Db):
    return await svc.create_asset(db, body)


@router.patch("/assets/{asset_id}", response_model=AssetOut)
async def update_asset(asset_id: uuid.UUID, body: AssetUpdate, db: Db):
    asset = await _or_404(await svc.get_asset(db, asset_id), "Asset")
    return await svc.update_asset(db, asset, body)


@router.post("/assets/{asset_id}/{action}", response_model=AssetOut)
async def transition_asset(asset_id: uuid.UUID, action: str, db: Db):
    asset = await _or_404(await svc.get_asset(db, asset_id), "Asset")
    return await svc.transition(db, asset, _normalize_action(action))


# --- Items ---
@router.post("/items", response_model=ItemOut, status_code=201)
async def create_item(body: ItemCreate, db: Db):
    return await svc.create_item(db, body)


@router.get("/items", response_model=list[ItemOut])
async def list_items(
    db: Db,
    status_filter: CurriculumStatus | None = None,
    concept_id: uuid.UUID | None = None,
    skill_id: uuid.UUID | None = None,
    kind: ItemKind | None = None,
):
    return await svc.list_items(
        db, status_filter=status_filter, concept_id=concept_id, skill_id=skill_id, kind=kind
    )


@router.get("/review", response_model=list[ItemOut])
async def review_queue(db: Db):
    # Items awaiting a human decision.
    drafts = await svc.list_items(db, status_filter=CurriculumStatus.draft)
    reviewed = await svc.list_items(db, status_filter=CurriculumStatus.reviewed)
    return reviewed + drafts


@router.get("/items/{item_id}", response_model=ItemOut)
async def get_item(item_id: uuid.UUID, db: Db):
    return await _or_404(await svc.get_item(db, item_id), "Item")


@router.patch("/items/{item_id}", response_model=ItemOut)
async def update_item(item_id: uuid.UUID, body: ItemUpdate, db: Db):
    item = await _or_404(await svc.get_item(db, item_id), "Item")
    return await svc.update_item(db, item, body)


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: uuid.UUID, db: Db):
    item = await _or_404(await svc.get_item(db, item_id), "Item")
    await svc.delete_item(db, item)


@router.post("/items/{item_id}/{action}", response_model=ItemOut)
async def transition_item(item_id: uuid.UUID, action: str, db: Db):
    item = await _or_404(await svc.get_item(db, item_id), "Item")
    return await svc.transition(db, item, _normalize_action(action))


# --- Book maps ---
@router.post("/book-maps", response_model=BookMapOut, status_code=201)
async def create_book_map(body: BookMapCreate, db: Db):
    return await svc.create_book_map(db, body)


@router.get("/book-maps", response_model=list[BookMapOut])
async def list_book_maps(db: Db):
    return await svc.list_book_maps(db)


def _normalize_action(action: str) -> str:
    key = action.replace("-", "_")
    if key not in svc._TRANSITIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown action '{action}'.")
    return key
