import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.checkin import checkin_logic
from app.models import Message, CheckinTrajectoryResponseCreate

class CheckinConversationMessage(BaseModel):
    role: Literal["user", "assistant", "prompt"]
    text: str


router = APIRouter(prefix="/checkins", tags=["checkins"])


class CheckinRequest(BaseModel):
    type: Literal["morning", "evening"]
    text: str
    trajectory_responses: list[CheckinTrajectoryResponseCreate] | None = None
    messages: list[CheckinConversationMessage] | None = None


class CheckinResponse(BaseModel):
    reply: str
    checkin_id: str
    messages: list[CheckinConversationMessage] = []


class CheckinPublic(BaseModel):
    id: uuid.UUID
    type: Literal["morning", "evening"]
    text: str
    reply: str
    created_at: datetime
    alignment_score: int | None = None
    onboarding_id: str | None = None
    morning_id: str | None = None
    messages: list[CheckinConversationMessage] = []


class CheckinsPublic(BaseModel):
    data: list[CheckinPublic]
    count: int


class CheckinUpdate(BaseModel):
    text: str
    messages: list[CheckinConversationMessage] | None = None


@router.post("/", response_model=CheckinResponse)
def create_checkin(
    *, session: SessionDep, current_user: CurrentUser, payload: CheckinRequest
) -> CheckinResponse:
    tr_responses = None
    if payload.trajectory_responses:
        tr_responses = [tr.model_dump() for tr in payload.trajectory_responses]
        
    checkin = checkin_logic.create(
        session=session,
        user_id=current_user.id,
        checkin_type=payload.type,
        text=payload.text,
        trajectory_responses=tr_responses,
        session_messages=[m.model_dump() for m in payload.messages] if payload.messages else None,
    )
    reply, messages = checkin_logic.parse_reply_payload(
        user_text=checkin.text,
        reply=checkin.reply,
    )
    return CheckinResponse(reply=reply, checkin_id=str(checkin.id), messages=messages)


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
            # Keep the list API backward-compatible while exposing structured conversation when available.
            # Frontend can render this as a thread instead of a single reflection block.
            CheckinPublic(
                id=checkin.id,
                type=checkin.type,
                text=checkin.text,
                reply=checkin_logic.parse_reply_payload(
                    user_text=checkin.text,
                    reply=checkin.reply,
                )[0],
                created_at=checkin.created_at,
                alignment_score=checkin.alignment_score,
                onboarding_id=checkin.onboarding_id,
                morning_id=checkin.morning_id,
                messages=checkin_logic.parse_reply_payload(
                    user_text=checkin.text,
                    reply=checkin.reply,
                )[1],
            )
        )

    return CheckinsPublic(data=data, count=count)


@router.get("/timeline", response_model=CheckinsPublic)
def read_checkin_timeline(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    days: int = 7,
) -> CheckinsPublic:
    """
    Retrieve checkins for the current user for the last `days`.
    """
    checkins = checkin_logic.read_timeline(
        session=session,
        user_id=current_user.id,
        days=days,
    )

    data = []
    for checkin in checkins:
        data.append(
            CheckinPublic(
                id=checkin.id,
                type=checkin.type,
                text=checkin.text,
                reply=checkin_logic.parse_reply_payload(
                    user_text=checkin.text,
                    reply=checkin.reply,
                )[0],
                created_at=checkin.created_at,
                alignment_score=checkin.alignment_score,
                onboarding_id=checkin.onboarding_id,
                morning_id=checkin.morning_id,
                messages=checkin_logic.parse_reply_payload(
                    user_text=checkin.text,
                    reply=checkin.reply,
                )[1],
            )
        )

    return CheckinsPublic(data=data, count=len(data))


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

    reply, messages = checkin_logic.parse_reply_payload(
        user_text=checkin.text,
        reply=checkin.reply,
    )
    return CheckinPublic(
        id=checkin.id,
        type=checkin.type,
        text=checkin.text,
        reply=reply,
        created_at=checkin.created_at,
        alignment_score=checkin.alignment_score,
        onboarding_id=checkin.onboarding_id,
        morning_id=checkin.morning_id,
        messages=messages,
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
    Update a checkin's text. The AI reply is regenerated with the updated context.
    """
    checkin = checkin_logic.read(session=session, checkin_id=checkin_id)
    if not checkin:
        raise HTTPException(status_code=404, detail="Checkin not found")

    # Verify ownership
    if checkin.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    checkin = checkin_logic.update(
        session=session,
        db_checkin=checkin,
        text=checkin_in.text,
        session_messages=[m.model_dump() for m in checkin_in.messages] if checkin_in.messages else None,
    )

    reply, messages = checkin_logic.parse_reply_payload(
        user_text=checkin.text,
        reply=checkin.reply,
    )
    return CheckinPublic(
        id=checkin.id,
        type=checkin.type,
        text=checkin.text,
        reply=reply,
        created_at=checkin.created_at,
        alignment_score=checkin.alignment_score,
        onboarding_id=checkin.onboarding_id,
        morning_id=checkin.morning_id,
        messages=messages,
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
