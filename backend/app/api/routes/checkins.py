from datetime import datetime, timezone
import re
from typing import Any, Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import desc, select

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.models import QuestionnaireResponse

router = APIRouter(prefix="/checkins", tags=["checkins"])


class CheckinRequest(BaseModel):
    type: Literal["morning", "evening"]
    text: str


class CheckinResponse(BaseModel):
    reply: str
    checkin_id: str


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
    onboarding = session.exec(
        select(QuestionnaireResponse)
        .where(
            QuestionnaireResponse.owner_id == current_user.id,
            QuestionnaireResponse.kind == "onboarding",
        )
        .order_by(desc(QuestionnaireResponse.created_at))
    ).first()

    last_morning = None
    if payload.type == "evening":
        last_morning = session.exec(
            select(QuestionnaireResponse)
            .where(
                QuestionnaireResponse.owner_id == current_user.id,
                QuestionnaireResponse.kind == "morning_checkin",
            )
            .order_by(desc(QuestionnaireResponse.created_at))
        ).first()

    prompt = _build_prompt(
        checkin_type=payload.type,
        checkin_text=payload.text,
        onboarding_payload=onboarding.payload if onboarding else None,
        last_morning_text=(last_morning.payload.get("text") if last_morning else None),
    )

    reply = _call_llm(prompt)
    if reply is None:
        reply = _fallback_reply(
            checkin_type=payload.type,
            checkin_text=payload.text,
            onboarding_payload=onboarding.payload if onboarding else None,
            last_morning_text=(last_morning.payload.get("text") if last_morning else None),
        )

    alignment_score = None
    if payload.type == "evening":
        domains = _extract_domains(onboarding.payload if onboarding else None)
        missing = _missing_domains(payload.text, domains, threshold=7)
        if domains:
            mentioned = max(len(domains) - len(missing), 0)
            alignment_score = min(100, 45 + mentioned * 8)

    response_payload = {
        "type": payload.type,
        "text": payload.text,
        "reply": reply,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "onboarding_id": str(onboarding.id) if onboarding else None,
        "morning_id": str(last_morning.id) if last_morning else None,
        "alignment_score": alignment_score,
    }

    response = QuestionnaireResponse.model_validate(
        {
            "kind": f"{payload.type}_checkin",
            "schema_version": "v1",
            "payload": response_payload,
            "owner_id": current_user.id,
        }
    )
    session.add(response)
    session.commit()
    session.refresh(response)

    return CheckinResponse(reply=reply, checkin_id=str(response.id))
