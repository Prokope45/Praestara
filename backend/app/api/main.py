from fastapi import APIRouter

from app.api.routes import ai, checkins, engine89, items, login, orientations, private, questionnaires, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(orientations.router)
api_router.include_router(questionnaires.router, prefix="/questionnaires", tags=["questionnaires"])
api_router.include_router(ai.router)
api_router.include_router(engine89.router)
api_router.include_router(checkins.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
