from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, SessionDep
from app.goal_scaffold.alignment import service
from app.goal_scaffold.alignment.models import (
    AlignmentDailyRequest,
    AlignmentDailyPostResponse,
    AlignmentDailyResponse,
    AlignmentHistoryEntry,
    AlignmentHistoryResponse,
    AlignmentWeeklyMeetingRequest,
    AlignmentWeeklyMeetingResponse,
    AlignmentWeeklySummaryResponse,
)

router = APIRouter()


@router.get("/daily", response_model=AlignmentDailyResponse)
def get_daily_alignment(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    day: date | None = Query(default=None),
) -> AlignmentDailyResponse:
    target_day = day or date.today()
    commitments = service.get_daily_commitments(session, current_user.id, target_day)
    return AlignmentDailyResponse(date=target_day, commitments=commitments)


@router.post("/daily", response_model=AlignmentDailyPostResponse)
def post_daily_alignment(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: AlignmentDailyRequest,
) -> AlignmentDailyPostResponse:
    try:
        results = service.submit_daily_reflection(
            session, current_user.id, body.date, body.commitments_completed
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.commit()
    return AlignmentDailyPostResponse(date=body.date, results=results)


@router.get("/weekly-summary", response_model=AlignmentWeeklySummaryResponse)
def get_weekly_summary(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    week_start: date = Query(...),
) -> AlignmentWeeklySummaryResponse:
    summaries = service.get_weekly_summary(session, current_user.id, week_start)
    return AlignmentWeeklySummaryResponse(week_start=week_start, summaries=summaries)


@router.get("/history", response_model=AlignmentHistoryResponse)
def get_alignment_history(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> AlignmentHistoryResponse:
    timeline = service.get_alignment_history(session, current_user.id)
    return AlignmentHistoryResponse(
        timeline=[AlignmentHistoryEntry(**entry) for entry in timeline]
    )


@router.post("/weekly-meeting", response_model=AlignmentWeeklyMeetingResponse)
def post_weekly_meeting(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: AlignmentWeeklyMeetingRequest,
) -> AlignmentWeeklyMeetingResponse:
    try:
        results = service.submit_weekly_meeting(
            session, current_user.id, body.week_start, body.adjustments
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.commit()
    return AlignmentWeeklyMeetingResponse(week_start=body.week_start, results=results)
