import re
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import desc, func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.models import Checkin, Message, QuestionnaireResponse, QuestionnaireAssignment, QuestionnaireTemplate

router = APIRouter(prefix="/checkins", tags=["checkins"])

def _get_onboarding_payload(session: SessionDep, user_id: uuid.UUID) -> tuple[dict[str, Any] | None, str | None]:
    statement = (
        select(QuestionnaireResponse)
        .join(QuestionnaireAssignment)
        .join(QuestionnaireTemplate)
        .where(
            QuestionnaireResponse.user_id == user_id,
            QuestionnaireTemplate.title == "Praestara Onboarding"
        )
        .order_by(desc(QuestionnaireResponse.completed_at))
    )
    response = session.exec(statement).first()
    
    if not response:
        return None, None
        
    payload = {"sectionB": {"domains": []}}
    # Fetch questions and answers
    for answer in response.answers:
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
            
    return payload, str(response.id)


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


def _build_prompt(
    *,
    checkin_type: str,
    checkin_text: str,
    onboarding_payload: dict[str, Any] | None,
    last_morning_text: str | None,
) -> str:
    context_parts = [
        "You are Praestara: non-moralizing, values-anchored, non-diagnostic.",
        "Your goal is to connect actions to values and self-concept, without accountability or judgment.",
        "If there are discrepancies between stated values and today's plan/summary, gently reflect them without questions.",
        "Close with a short glimpse of how today's direction reinforces who the person is becoming.",
    ]

    if onboarding_payload:
        context_parts.append("Onboarding values/self-concept data (JSON):")
        context_parts.append(str(onboarding_payload))

    if checkin_type == "morning":
        context_parts.append("Morning check-in (user plans):")
        context_parts.append(checkin_text)
        context_parts.append(
            "Respond with: (1) a brief reflection, (2) a closing glimpse of how this direction supports the identity trajectory. No questions."
        )
    else:
        if last_morning_text:
            context_parts.append("Morning plan (earlier today):")
            context_parts.append(last_morning_text)
        context_parts.append("Evening check-in (what they did today):")
        context_parts.append(checkin_text)
        context_parts.append(
            "Respond with: (1) a brief reflection comparing plan vs day, (2) a closing glimpse of how this supports identity trajectory. No questions."
        )

    return "\n\n".join(context_parts)


def _extract_domains(onboarding_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not onboarding_payload:
        return []
    section_b = onboarding_payload.get("sectionB", {})
    domains = section_b.get("domains", [])
    return [domain for domain in domains if isinstance(domain, dict)]


def _tokenize_domain(name: str) -> list[str]:
    parts = re.split(r"[,&/]|\\band\\b", name.lower())
    return [token.strip() for token in parts if token.strip()]


def _missing_domains(
    text: str, domains: list[dict[str, Any]], *, threshold: int = 7
) -> list[str]:
    lowered = text.lower()
    missing: list[str] = []
    for domain in domains:
        importance = domain.get("importance")
        if not isinstance(importance, (int, float)) or importance < threshold:
            continue
        name = str(domain.get("name", "")).strip()
        if not name:
            continue
        tokens = _tokenize_domain(name)
        if tokens and not any(token in lowered for token in tokens):
            missing.append(name)
    return missing


def _fallback_reply(
    *,
    checkin_type: str,
    checkin_text: str,
    onboarding_payload: dict[str, Any] | None,
    last_morning_text: str | None,
) -> str:
    domains = _extract_domains(onboarding_payload)
    missing = _missing_domains(checkin_text, domains)
    first_sentence = checkin_text.strip().split(".")[0].strip()
    if len(first_sentence) > 120:
        first_sentence = f"{first_sentence[:117]}..."

    if checkin_type == "morning":
        lines = [
            f"Thanks for sharing. I hear your plan: {first_sentence or 'today matters to you.'}",
        ]
        if missing:
            lines.append(
                f"Today leans away from {missing[0]}; that's a signal worth holding gently."
            )
        lines.append("This kind of day reinforces the person who protects what matters and moves with intention.")
        return " ".join(lines)

    lines = []
    if last_morning_text:
        morning_snippet = last_morning_text.strip().split(".")[0].strip()
        if len(morning_snippet) > 120:
            morning_snippet = f"{morning_snippet[:117]}..."
        lines.append(f"This morning you planned: {morning_snippet}.")
    lines.append(f"This evening you shared: {first_sentence or 'today had its own shape.'}.")
    if missing:
        lines.append(f"Today leaned away from {missing[0]}; the shift is informative, not a failure.")
    lines.append("These reflections accumulate into a steadier identity trajectory over time.")
    return " ".join(lines)


def _call_llm(prompt: str) -> str | None:
    if not settings.LLM_ENDPOINT:
        return None

    headers: dict[str, str] = {}
    if settings.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"

    request_body = {
        "prompt": prompt,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "temperature": settings.LLM_TEMPERATURE,
    }

    timeout_seconds = min(settings.LLM_TIMEOUT_SECONDS, 8)
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(str(settings.LLM_ENDPOINT), json=request_body, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError:
        return None

    data = response.json()
    reply = data.get("output") or data.get("reply") or data.get("text")
    if not reply:
        return None
    return str(reply)


@router.post("/", response_model=CheckinResponse)
def create_checkin(
    *, session: SessionDep, current_user: CurrentUser, payload: CheckinRequest
) -> CheckinResponse:
    onboarding_payload, onboarding_id = _get_onboarding_payload(session, current_user.id)

    last_morning = None
    if payload.type == "evening":
        last_morning = session.exec(
            select(Checkin)
            .where(
                Checkin.user_id == current_user.id,
                Checkin.type == "morning",
            )
            .order_by(desc(Checkin.created_at))
        ).first()

    prompt = _build_prompt(
        checkin_type=payload.type,
        checkin_text=payload.text,
        onboarding_payload=onboarding_payload,
        last_morning_text=(last_morning.text if last_morning else None),
    )

    reply = _call_llm(prompt)
    if reply is None:
        reply = _fallback_reply(
            checkin_type=payload.type,
            checkin_text=payload.text,
            onboarding_payload=onboarding_payload,
            last_morning_text=(last_morning.text if last_morning else None),
        )

    alignment_score = None
    if payload.type == "evening":
        domains = _extract_domains(onboarding_payload)
        missing = _missing_domains(payload.text, domains, threshold=7)
        if domains:
            mentioned = max(len(domains) - len(missing), 0)
            alignment_score = min(100, 45 + mentioned * 8)

    response = Checkin(
        type=payload.type,
        text=payload.text,
        reply=reply,
        user_id=current_user.id,
        alignment_score=alignment_score,
        onboarding_id=onboarding_id,
        morning_id=str(last_morning.id) if last_morning else None,
    )
    session.add(response)
    session.commit()
    session.refresh(response)

    return CheckinResponse(reply=reply, checkin_id=str(response.id))


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
    # Build the base query
    if type:
        count_statement = (
            select(func.count())
            .select_from(Checkin)
            .where(
                Checkin.user_id == current_user.id,
                Checkin.type == type,
            )
        )
        statement = (
            select(Checkin)
            .where(
                Checkin.user_id == current_user.id,
                Checkin.type == type,
            )
            .order_by(desc(Checkin.created_at))
            .offset(skip)
            .limit(limit)
        )
    else:
        count_statement = (
            select(func.count())
            .select_from(Checkin)
            .where(
                Checkin.user_id == current_user.id,
                Checkin.type.in_(["morning", "evening"]),
            )
        )
        statement = (
            select(Checkin)
            .where(
                Checkin.user_id == current_user.id,
                Checkin.type.in_(["morning", "evening"]),
            )
            .order_by(desc(Checkin.created_at))
            .offset(skip)
            .limit(limit)
        )

    count = session.exec(count_statement).one()
    checkins = session.exec(statement).all()

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
    checkin = session.get(Checkin, checkin_id)
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
    checkin = session.get(Checkin, checkin_id)
    if not checkin:
        raise HTTPException(status_code=404, detail="Checkin not found")

    # Verify ownership
    if checkin.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    checkin.text = checkin_in.text
    session.add(checkin)
    session.commit()
    session.refresh(checkin)

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
    checkin = session.get(Checkin, checkin_id)
    if not checkin:
        raise HTTPException(status_code=404, detail="Checkin not found")

    # Verify ownership
    if checkin.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    session.delete(checkin)
    session.commit()

    return Message(message="Checkin deleted successfully")
