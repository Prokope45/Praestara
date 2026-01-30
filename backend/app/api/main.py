from fastapi import APIRouter

<<<<<<< HEAD
from app.api.routes import ai, checkins, engine89, items, login, orientations, private, questionnaires, users, utils
=======
from app.api.routes import items, login, orientations, private, users, utils, questionnaires
>>>>>>> 143f201b1c0eb0505243029a56878d6568d99d9f
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(orientations.router)
<<<<<<< HEAD
api_router.include_router(questionnaires.router)
api_router.include_router(ai.router)
api_router.include_router(engine89.router)
api_router.include_router(checkins.router)
=======
api_router.include_router(questionnaires.router, prefix="/questionnaires", tags=["questionnaires"])
>>>>>>> 143f201b1c0eb0505243029a56878d6568d99d9f


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
