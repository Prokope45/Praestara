import hashlib
import hmac
import json
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
import httpx

from app.models import (
    Engine89Result,
    Engine89ResultCreate,
    Engine89ResultPublic,
    Engine89ResultsPublic,
    Message,
    Checkin,
    QuestionnaireResponse,
)

router = APIRouter(prefix="/engine89", tags=["engine89"])


def _subject_hash(user_id: uuid.UUID) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(),
        msg=str(user_id).encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()


@router.get("/export", response_model=dict[str, Any])
def export_for_engine89(
    session: SessionDep,
    current_user: CurrentUser,
    kind: str | None = None,
) -> Any:
    """
    Export de-identified questionnaire payloads for Engine89.
    """
    export_data = []

    # Checkins
    if current_user.is_superuser:
        c_statement = select(Checkin)
        if kind and kind.endswith("_checkin"):
            c_statement = c_statement.where(Checkin.type == kind.replace("_checkin", ""))
    else:
        c_statement = select(Checkin).where(Checkin.user_id == current_user.id)
        if kind and kind.endswith("_checkin"):
            c_statement = c_statement.where(Checkin.type == kind.replace("_checkin", ""))

    if not kind or kind.endswith("_checkin"):
        checkins = session.exec(c_statement).all()
        for checkin in checkins:
            export_data.append({
                "subject_hash": _subject_hash(checkin.user_id),
                "response_id": str(checkin.id),
                "kind": f"{checkin.type}_checkin",
                "schema_version": "v1",
                "created_at": checkin.created_at.isoformat(),
                "payload": {
                    "type": checkin.type,
                    "text": checkin.text,
                    "reply": checkin.reply,
                    "alignment_score": checkin.alignment_score,
                    "onboarding_id": checkin.onboarding_id,
                    "morning_id": checkin.morning_id
                }
            })

    # QuestionnaireResponses
    if current_user.is_superuser:
        q_statement = select(QuestionnaireResponse)
    else:
        q_statement = select(QuestionnaireResponse).where(QuestionnaireResponse.user_id == current_user.id)

    if not kind or kind == "onboarding":
        q_responses = session.exec(q_statement).all()
        for q_resp in q_responses:
            if kind == "onboarding" and q_resp.assignment.questionnaire.title != "Praestara Onboarding":
                continue
            
            payload = {"sectionB": {"domains": []}}
            for answer in q_resp.answers:
                question = answer.question
                if question.scale_type == "DOMAIN_RATING":
                    payload["sectionB"]["domains"].append({
                        "name": question.question_text,
                        "importance": answer.likert_value
                    })
                elif question.scale_type == "TEXT":
                    payload[question.question_text] = answer.text_response
                elif question.scale_type in ("LIKERT_5", "LIKERT_7", "FREQUENCY"):
                    payload[question.question_text] = answer.likert_value
                    
            export_data.append({
                "subject_hash": _subject_hash(q_resp.user_id),
                "response_id": str(q_resp.id),
                "kind": "onboarding" if q_resp.assignment.questionnaire.title == "Praestara Onboarding" else "questionnaire",
                "schema_version": "v1",
                "created_at": q_resp.completed_at.isoformat(),
                "payload": payload
            })

    return {"data": export_data, "count": len(export_data)}


@router.post("/import", response_model=Message)
def import_engine89_results(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    results: list[Engine89ResultCreate],
) -> Message:
    """
    Import Engine89 results by subject_hash. Superusers only.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    users = session.exec(select(Engine89Result.owner_id.distinct())).all()
    user_ids_c = session.exec(select(Checkin.user_id.distinct())).all()
    user_ids_q = session.exec(select(QuestionnaireResponse.user_id.distinct())).all()
    candidate_ids = set(users) | set(user_ids_c) | set(user_ids_q)

    hash_map = {_subject_hash(user_id): user_id for user_id in candidate_ids}

    created = 0
    for result in results:
        if not result.subject_hash:
            continue
        owner_id = hash_map.get(result.subject_hash)
        if not owner_id:
            continue
        db_result = Engine89Result.model_validate(
            result, update={"owner_id": owner_id}
        )
        session.add(db_result)
        created += 1

    session.commit()
    return Message(message=f"Imported {created} Engine89 results")


@router.post("/run", response_model=Message)
def run_engine89(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    kind: str | None = None,
) -> Message:
    """
    Export data to Project89 and store returned Engine89 results.
    """
    if not settings.PROJECT89_ENDPOINT:
        raise HTTPException(status_code=503, detail="Project89 endpoint not configured")

    export_payload = export_for_engine89(session, current_user, kind)

    headers: dict[str, str] = {}
    if settings.PROJECT89_API_KEY:
        headers["Authorization"] = f"Bearer {settings.PROJECT89_API_KEY}"

    try:
        with httpx.Client(timeout=settings.PROJECT89_TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{settings.PROJECT89_ENDPOINT}/api/engine/run",
                json={"text": json.dumps(export_payload)},
                headers=headers,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Project89 request failed: {exc}") from exc

    data = response.json()
    engine_report = data.get("engine_report") or {}
    results_payload = [
        Engine89ResultCreate(
            subject_hash=_subject_hash(current_user.id),
            kind="engine89",
            schema_version="v1",
            payload=engine_report,
        )
    ]

    import_engine89_results(
        session=session, current_user=current_user, results=results_payload
    )

    return Message(message="Engine89 run complete")


@router.get("/results", response_model=Engine89ResultsPublic)
def read_engine89_results(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve Engine89 results.
    """
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Engine89Result)
        statement = select(Engine89Result)
    else:
        count_statement = (
            select(func.count())
            .select_from(Engine89Result)
            .where(Engine89Result.owner_id == current_user.id)
        )
        statement = select(Engine89Result).where(
            Engine89Result.owner_id == current_user.id
        )

    count = session.exec(count_statement).one()
    results = session.exec(statement.offset(skip).limit(limit)).all()
    return Engine89ResultsPublic(data=results, count=count)
