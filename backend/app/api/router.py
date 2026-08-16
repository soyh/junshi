from fastapi import APIRouter

from app.api.routes.persons import router as persons_router
from app.api.routes.relationships import router as relationships_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(persons_router)
api_router.include_router(relationships_router)
