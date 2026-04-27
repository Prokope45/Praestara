from app.koios_client import ai_router
from fastapi import APIRouter

from app.api.routes import checkins, engine89, login, private, questionnaires, trajectories, users, utils
from app.besci.routes import router as besci_router
from app.core.config import settings
from app.goal_scaffold.router import goal_scaffold_router

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(questionnaires.router, prefix="/questionnaires", tags=["questionnaires"])
api_router.include_router(goal_scaffold_router, prefix="/scaffold", tags=["goal-scaffold"])
api_router.include_router(besci_router)
api_router.include_router(ai_router)
api_router.include_router(engine89.router)
api_router.include_router(checkins.router)
api_router.include_router(trajectories.router, prefix="/trajectories", tags=["trajectories"])


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
