from fastapi import APIRouter

from app.api.routes import ai, app_flow, checkins, engine89, items, login, orientations, private, programs, questionnaires, users, utils
from app.goal_scaffold.alignment.routes import router as alignment_router
from app.core.config import settings
from app.goal_scaffold.router import goal_scaffold_router

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(orientations.router)
api_router.include_router(questionnaires.router, prefix="/questionnaires", tags=["questionnaires"])
api_router.include_router(app_flow.flow_router, prefix="/app", tags=["app-flow"])
api_router.include_router(app_flow.week_setup_router, prefix="/week-setup", tags=["week-setup"])
api_router.include_router(goal_scaffold_router, prefix="/scaffold", tags=["goal-scaffold"])
api_router.include_router(alignment_router, prefix="/alignment", tags=["alignment"])
api_router.include_router(ai.router)
api_router.include_router(engine89.router)
api_router.include_router(checkins.router)
api_router.include_router(programs.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
