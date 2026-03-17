import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.checkin import checkin_logic
from app.models import Message

router = APIRouter(prefix="/checkins", tags=["checkins"])


class CheckinRequest(BaseModel):
    type: Literal["morning", "evening"]
    text: str


class CheckinResponse(BaseModel):
    reply: str
    checkin_id: str


class CheckinPublic(BaseModel):
    id: uuid.UUID
    type: Literal["morning", "evening"]
    text: str
    reply: str
    created_at: datetime
    alignment_score: int | None = None
    onboarding_id: str | None = None
    morning_id: str | None = None


class CheckinsPublic(BaseModel):
    data: list[CheckinPublic]
    count: int


class CheckinUpdate(BaseModel):
    text: str


@router.post("/", response_model=CheckinResponse)
def create_checkin(
    *, session: SessionDep, current_user: CurrentUser, payload: CheckinRequest
) -> CheckinResponse:
    checkin = checkin_logic.create(
        session=session,
        user_id=current_user.id,
        checkin_type=payload.type,
        text=payload.text,
    )
    return CheckinResponse(reply=checkin.reply, checkin_id=str(checkin.id))


@router.get("/", response_model=CheckinsPublic)
def read_checkins(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    type: Literal["morning", "evening"] | None = None,
) -> CheckinsPublic:
    """
    Retrieve checkins for the current user.
    Optionally filter by type (morning or evening).
    """
    checkins, count = checkin_logic.read_all(
        session=session,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        type=type,
    )

    # Transform to CheckinPublic format
    data = []
    for checkin in checkins:
        data.append(
            CheckinPublic(
                id=checkin.id,
                type=checkin.type,
                text=checkin.text,
                reply=checkin.reply,
                created_at=checkin.created_at,
                alignment_score=checkin.alignment_score,
                onboarding_id=checkin.onboarding_id,
                morning_id=checkin.morning_id,
            )
        )

    return CheckinsPublic(data=data, count=count)


@router.get("/{checkin_id}", response_model=CheckinPublic)
def read_checkin(
    *, session: SessionDep, current_user: CurrentUser, checkin_id: uuid.UUID
) -> CheckinPublic:
    """
    Get a specific checkin by ID.
    """
    checkin = checkin_logic.read(session=session, checkin_id=checkin_id)
    if not checkin:
        raise HTTPException(status_code=404, detail="Checkin not found")

    # Verify ownership
    if checkin.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return CheckinPublic(
        id=checkin.id,
        type=checkin.type,
        text=checkin.text,
        reply=checkin.reply,
        created_at=checkin.created_at,
        alignment_score=checkin.alignment_score,
        onboarding_id=checkin.onboarding_id,
        morning_id=checkin.morning_id,
    )


@router.patch("/{checkin_id}", response_model=CheckinPublic)
def update_checkin(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    checkin_id: uuid.UUID,
    checkin_in: CheckinUpdate,
) -> CheckinPublic:
    """
    Update a checkin's text. The AI reply is not regenerated.
    """
    checkin = checkin_logic.read(session=session, checkin_id=checkin_id)
    if not checkin:
        raise HTTPException(status_code=404, detail="Checkin not found")

    # Verify ownership
    if checkin.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    checkin = checkin_logic.update(session=session, db_checkin=checkin, text=checkin_in.text)

    return CheckinPublic(
        id=checkin.id,
        type=checkin.type,
        text=checkin.text,
        reply=checkin.reply,
        created_at=checkin.created_at,
        alignment_score=checkin.alignment_score,
        onboarding_id=checkin.onboarding_id,
        morning_id=checkin.morning_id,
    )


@router.delete("/{checkin_id}", response_model=Message)
def delete_checkin(
    *, session: SessionDep, current_user: CurrentUser, checkin_id: uuid.UUID
) -> Message:
    """
    Delete a checkin.
    """
    checkin = checkin_logic.read(session=session, checkin_id=checkin_id)
    if not checkin:
        raise HTTPException(status_code=404, detail="Checkin not found")

    # Verify ownership
    if checkin.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = checkin_logic.delete(session=session, db_checkin=checkin)

    if result.get("isDeleted"):
        return Message(message="Checkin deleted successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete checkin")
