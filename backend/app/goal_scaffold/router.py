from fastapi import APIRouter

from app.goal_scaffold.self_concept.routes import router as self_concept_router
from app.goal_scaffold.goals.routes import router as goals_router
from app.goal_scaffold.habits.routes import router as habits_router
from app.goal_scaffold.health.routes import router as health_router
from app.goal_scaffold.nutrition.routes import router as nutrition_router
from app.goal_scaffold.weekly_cycle.routes import router as weekly_cycle_router
from app.goal_scaffold.stability.routes import router as stability_router
from app.goal_scaffold.resource_profile.routes import router as resource_profile_router
from app.goal_scaffold.trajectory.routes import router as trajectory_router
from app.goal_scaffold.metrics.routes import router as metrics_router

goal_scaffold_router = APIRouter()

goal_scaffold_router.include_router(
    self_concept_router, prefix="/self-concept", tags=["goal-scaffold: self-concept"]
)
goal_scaffold_router.include_router(
    goals_router, prefix="/goals", tags=["goal-scaffold: goals"]
)
goal_scaffold_router.include_router(
    habits_router, prefix="/habits", tags=["goal-scaffold: habits"]
)
goal_scaffold_router.include_router(
    health_router, prefix="/health", tags=["goal-scaffold: health"]
)
goal_scaffold_router.include_router(
    nutrition_router, prefix="/nutrition", tags=["goal-scaffold: nutrition"]
)
goal_scaffold_router.include_router(
    weekly_cycle_router, prefix="/weekly", tags=["goal-scaffold: weekly-cycle"]
)
goal_scaffold_router.include_router(
    stability_router, prefix="/stability", tags=["goal-scaffold: stability"]
)
goal_scaffold_router.include_router(
    resource_profile_router, prefix="/resources", tags=["goal-scaffold: resources"]
)
goal_scaffold_router.include_router(
    trajectory_router, prefix="/trajectory", tags=["goal-scaffold: trajectory"]
)
goal_scaffold_router.include_router(
    metrics_router, prefix="/metrics", tags=["goal-scaffold: metrics"]
)
