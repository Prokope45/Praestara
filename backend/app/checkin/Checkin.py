import re
import uuid
from typing import Any

import httpx
from sqlmodel import Session, desc, func, select

from app.core.config import settings
from app.models import (
    Checkin,
    QuestionnaireAssignment,
    QuestionnaireResponse,
    QuestionnaireTemplate,
)


class CheckinLogic:

    _instance = None

    def __init__(self) -> None:
        """Deny instantiation of class."""
        return None

    def __new__(cls):
        """Instantiates singleton if none exist yet."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_onboarding_payload(self, session: Session, user_id: uuid.UUID) -> tuple[dict[str, Any] | None, str | None]:
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

    def _build_prompt(
        self,
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

    def _extract_domains(self, onboarding_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not onboarding_payload:
            return []
        section_b = onboarding_payload.get("sectionB", {})
        domains = section_b.get("domains", [])
        return [domain for domain in domains if isinstance(domain, dict)]

    def _tokenize_domain(self, name: str) -> list[str]:
        parts = re.split(r"[,&/]|\\band\\b", name.lower())
        return [token.strip() for token in parts if token.strip()]

    def _missing_domains(
        self, text: str, domains: list[dict[str, Any]], *, threshold: int = 7
    ) -> list[str]:
        lowered = text.lower()
        missing: list[str] = []
        for domain in domains:
            importance = domain.get("importance")
            if not isinstance(importance, int | float) or importance < threshold:
                continue
            name = str(domain.get("name", "")).strip()
            if not name:
                continue
            tokens = self._tokenize_domain(name)
            if tokens and not any(token in lowered for token in tokens):
                missing.append(name)
        return missing

    def _fallback_reply(
        self,
        *,
        checkin_type: str,
        checkin_text: str,
        onboarding_payload: dict[str, Any] | None,
        last_morning_text: str | None,
    ) -> str:
        domains = self._extract_domains(onboarding_payload)
        missing = self._missing_domains(checkin_text, domains)
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

    def _call_llm(self, prompt: str) -> str | None:
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

    def create(self, *, session: Session, user_id: uuid.UUID, checkin_type: str, text: str) -> Checkin:
        onboarding_payload, onboarding_id = self._get_onboarding_payload(session, user_id)

        last_morning = None
        if checkin_type == "evening":
            last_morning = session.exec(
                select(Checkin)
                .where(
                    Checkin.user_id == user_id,
                    Checkin.type == "morning",
                )
                .order_by(desc(Checkin.created_at))
            ).first()

        prompt = self._build_prompt(
            checkin_type=checkin_type,
            checkin_text=text,
            onboarding_payload=onboarding_payload,
            last_morning_text=(last_morning.text if last_morning else None),
        )

        reply = self._call_llm(prompt)
        if reply is None:
            reply = self._fallback_reply(
                checkin_type=checkin_type,
                checkin_text=text,
                onboarding_payload=onboarding_payload,
                last_morning_text=(last_morning.text if last_morning else None),
            )

        alignment_score = None
        if checkin_type == "evening":
            domains = self._extract_domains(onboarding_payload)
            missing = self._missing_domains(text, domains, threshold=7)
            if domains:
                mentioned = max(len(domains) - len(missing), 0)
                alignment_score = min(100, 45 + mentioned * 8)

        response = Checkin(
            type=checkin_type,
            text=text,
            reply=reply,
            user_id=user_id,
            alignment_score=alignment_score,
            onboarding_id=onboarding_id,
            morning_id=str(last_morning.id) if last_morning else None,
        )
        session.add(response)
        session.commit()
        session.refresh(response)

        return response

    def read_all(
        self, *, session: Session, user_id: uuid.UUID, skip: int, limit: int, type: str | None
    ) -> tuple[list[Checkin], int]:
        if type:
            count_statement = (
                select(func.count())
                .select_from(Checkin)
                .where(
                    Checkin.user_id == user_id,
                    Checkin.type == type,
                )
            )
            statement = (
                select(Checkin)
                .where(
                    Checkin.user_id == user_id,
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
                    Checkin.user_id == user_id,
                    Checkin.type.in_(["morning", "evening"]),
                )
            )
            statement = (
                select(Checkin)
                .where(
                    Checkin.user_id == user_id,
                    Checkin.type.in_(["morning", "evening"]),
                )
                .order_by(desc(Checkin.created_at))
                .offset(skip)
                .limit(limit)
            )

        count = session.exec(count_statement).one()
        checkins = session.exec(statement).all()
        return checkins, count

    def read(self, *, session: Session, checkin_id: uuid.UUID) -> Checkin | None:
        return session.get(Checkin, checkin_id)

    def update(self, *, session: Session, db_checkin: Checkin, text: str) -> Checkin:
        db_checkin.text = text
        session.add(db_checkin)
        session.commit()
        session.refresh(db_checkin)
        return db_checkin

    def delete(self, *, session: Session, db_checkin: Checkin) -> dict[str, bool]:
        is_deleted: bool = False
        try:
            session.delete(db_checkin)
            session.commit()
            is_deleted = True
        except Exception:
            is_deleted = False
        return {"isDeleted": is_deleted}
