from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.application.onboarding.dev_presets import PRESETS, apply_onboarding_preset
from app.core.security import get_password_hash
from app.models import (
    User,
    UserPublic,
)

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    is_verified: bool = False


class DevPresetApplyRequest(BaseModel):
    preset: str = "balanced_baseline"
    confirm_week_setup: bool = True


class DevPresetApplyResponse(BaseModel):
    preset: str
    assignment_id: str
    response_id: str
    cycle_id: str
    week_setup_confirmed: bool


@router.get("/dev/presets")
def list_dev_presets() -> dict[str, list[str]]:
    return {"presets": sorted(PRESETS.keys())}


@router.post("/dev/apply-onboarding-preset", response_model=DevPresetApplyResponse)
def apply_dev_onboarding_preset(
    body: DevPresetApplyRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    result = apply_onboarding_preset(
        session,
        current_user,
        preset_name=body.preset,
        confirm_week_setup=body.confirm_week_setup,
    )
    return DevPresetApplyResponse(**result)


@router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    """
    Create a new user.
    """

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )

    session.add(user)
    session.commit()

    return user
