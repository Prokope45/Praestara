from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.goal_scaffold.resource_profile import service
from app.goal_scaffold.resource_profile.models import (
    UserResourceProfilePublic,
    UserResourceProfileUpdate,
)

router = APIRouter(prefix="", tags=["resource-profile"])


@router.get("/profile", response_model=UserResourceProfilePublic)
def get_resource_profile(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    profile = service.get_or_create_profile(session, current_user.id)
    session.commit()
    session.refresh(profile)
    return profile


@router.put("/profile", response_model=UserResourceProfilePublic)
def update_resource_profile(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    profile_in: UserResourceProfileUpdate,
) -> Any:
    profile = service.update_profile(session, current_user.id, profile_in)
    session.commit()
    session.refresh(profile)
    return profile
