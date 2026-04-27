from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.besci.models import (
    BeSciAnalyzeRequest,
    BeSciAnalyzeResponse,
    BeSciHistoryPublic,
    BeSciSnapshot,
    BeSciSnapshotPublic,
)
from app.besci.service import (
    get_latest_snapshot,
    get_longitudinal_samples,
    get_snapshot_history,
)
from app.besci_client import besci_client
from app.core.config import settings

router = APIRouter(prefix="/besci", tags=["besci"])
STALE_THRESHOLD = timedelta(hours=12)


def _to_public(snapshot: BeSciSnapshot) -> BeSciSnapshotPublic:
    return BeSciSnapshotPublic(
        id=snapshot.id,
        user_id=snapshot.user_id,
        sample_count=snapshot.sample_count,
        checkin_sample_count=snapshot.checkin_sample_count,
        chat_sample_count=snapshot.chat_sample_count,
        trajectory_score=snapshot.trajectory_score,
        current_state=snapshot.current_state,
        baseline_state=snapshot.baseline_state,
        change_from_baseline=snapshot.change_from_baseline,
        summary=snapshot.summary,
        signals=snapshot.signals,
        computed_at=snapshot.computed_at,
    )


@router.post("/analyze", response_model=BeSciAnalyzeResponse)
def analyze_besci_payload(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    payload: BeSciAnalyzeRequest,
) -> BeSciAnalyzeResponse:
    analysis, _ = besci_client.analyze(
        payload.samples,
        user_id=current_user.id,
        allow_llm_summary=True,
    )
    return BeSciAnalyzeResponse(
        analysis=analysis
    )


@router.post("/demo/analyze", response_model=BeSciAnalyzeResponse)
def analyze_besci_demo(
    *,
    payload: BeSciAnalyzeRequest,
) -> BeSciAnalyzeResponse:
    if settings.ENVIRONMENT != "local":
        raise HTTPException(status_code=404, detail="Not found")
    analysis, _ = besci_client.analyze(payload.samples, allow_llm_summary=True)
    return BeSciAnalyzeResponse(analysis=analysis)


@router.get("/checkins", response_model=BeSciAnalyzeResponse)
def analyze_besci_checkins(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    days: int = 30,
    include_chat_history: bool = True,
) -> BeSciAnalyzeResponse:
    samples, _, _ = get_longitudinal_samples(
        session,
        current_user.id,
        days=days,
        include_chat_history=include_chat_history,
    )
    if not samples:
        raise HTTPException(
            status_code=404,
            detail="No longitudinal text found in the requested window for BeSci analysis",
        )
    analysis, _ = besci_client.analyze(
        samples,
        user_id=current_user.id,
        allow_llm_summary=True,
    )
    return BeSciAnalyzeResponse(analysis=analysis)


def _persist_snapshot_from_remote_or_local(
    *,
    session: SessionDep,
    user_id,
    days: int,
    include_chat_history: bool,
    allow_llm_summary: bool,
) -> BeSciSnapshot:
    samples, checkin_count, chat_count = get_longitudinal_samples(
        session,
        user_id,
        days=days,
        include_chat_history=include_chat_history,
    )
    if not samples:
        raise HTTPException(status_code=404, detail="No text samples available for BeSci snapshot")
    analysis, source = besci_client.analyze(
        samples,
        user_id=user_id,
        allow_llm_summary=allow_llm_summary,
    )
    snapshot = BeSciSnapshot(
        user_id=user_id,
        sample_count=analysis.sample_count,
        checkin_sample_count=checkin_count,
        chat_sample_count=chat_count,
        trajectory_score=analysis.trajectory_score,
        current_state=analysis.current_state.model_dump(mode="json"),
        baseline_state=analysis.baseline_state.model_dump(mode="json"),
        change_from_baseline=analysis.change_from_baseline.model_dump(mode="json"),
        summary=f"{analysis.summary}\nSource: {source}",
        signals=[signal.model_dump(mode="json") for signal in analysis.signals],
    )
    session.add(snapshot)
    session.flush()
    return snapshot


@router.post("/refresh", response_model=BeSciSnapshotPublic)
def refresh_besci_snapshot(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    days: int = 30,
    include_chat_history: bool = True,
) -> BeSciSnapshotPublic:
    snapshot = _persist_snapshot_from_remote_or_local(
        session=session,
        user_id=current_user.id,
        days=days,
        include_chat_history=include_chat_history,
        allow_llm_summary=True,
    )
    session.commit()
    session.refresh(snapshot)
    return _to_public(snapshot)


@router.get("/current", response_model=BeSciSnapshotPublic)
def get_current_besci_snapshot(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    days: int = 30,
    include_chat_history: bool = True,
) -> BeSciSnapshotPublic:
    snapshot = get_latest_snapshot(session, current_user.id)
    if snapshot is None or (datetime.utcnow() - snapshot.computed_at) > STALE_THRESHOLD:
        snapshot = _persist_snapshot_from_remote_or_local(
            session=session,
            user_id=current_user.id,
            days=days,
            include_chat_history=include_chat_history,
            allow_llm_summary=False,
        )
        session.commit()
        session.refresh(snapshot)
    return _to_public(snapshot)


@router.get("/history", response_model=BeSciHistoryPublic)
def get_besci_history(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = 20,
    offset: int = 0,
) -> BeSciHistoryPublic:
    snapshots = get_snapshot_history(session, current_user.id, limit=limit + offset)
    page = snapshots[offset : offset + limit]
    return BeSciHistoryPublic(data=[_to_public(snapshot) for snapshot in page], count=len(page))
