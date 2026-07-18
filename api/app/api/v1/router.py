from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.content import router as content_router
from app.api.v1.puzzles import router as puzzles_router
from app.api.v1.topics import router as topics_router
from app.api.v1.uploads import router as uploads_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(content_router)
api_v1_router.include_router(puzzles_router)
api_v1_router.include_router(topics_router)
api_v1_router.include_router(uploads_router)
