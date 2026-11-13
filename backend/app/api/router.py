"""
Root API router: mounts every module router.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.chat.router import router as chat_router
from app.modules.documents.router import router as documents_router
from app.modules.spaces.router import router as spaces_router
from app.modules.study.router import router as study_router
from app.modules.usage.router import router as usage_router
from app.modules.users.router import router as users_router

api_router = APIRouter(prefix="/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, tags=["users"])
api_router.include_router(spaces_router, prefix="/spaces", tags=["spaces"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(chat_router, prefix="/conversations", tags=["chat"])
api_router.include_router(study_router)  # /decks, /flashcards
api_router.include_router(usage_router, prefix="/usage", tags=["usage"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
