from fastapi import APIRouter
from .mindmap import router as mindmap_router
from app.config.settings import settings

router = APIRouter(prefix=settings.API_V1_STR)
router.include_router(mindmap_router) 