from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.checklist import router as checklist_router
from app.api.routes.clients import router as clients_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.proposals import router as proposals_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(clients_router)
api_router.include_router(proposals_router)
api_router.include_router(checklist_router)
api_router.include_router(documents_router)
api_router.include_router(dashboard_router)
