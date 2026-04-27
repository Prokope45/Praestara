import json
import re
import uuid
from typing import Any
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, desc, func, select

from app.besci_client import besci_client
from app.besci_local import BeSciTextSample
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

    def _build_analysis_payload(
        self,
        *,
        checkin_type: str,
        checkin_text: str,
        session_messages: list[dict[str, Any]] | None,
        onboarding_payload: dict[str, Any] | None,
        last_morning_text: str | None,
        besci_context: dict[str, Any] | None,
        trajectory_responses: list[dict[str, Any]] | None,
    ) -> tuple[str, list[dict[str, Any]]]:
        prompt_parts = [
            "You are Praestara: non-moralizing, values-anchored, non-diagnostic.",
            "Your goal is to connect the person's wording, current psychological mode, values, and self-concept without flattening them into generic encouragement.",
            "Ground every interpretation in the user's actual language plus the structured BeSci read when provided. Do not invent feelings, motives, or pathology.",
            "Interpret the whole check-in conversation as one session when multiple messages are present. Do not reduce the thread to only the last line.",
            "Write like a brief thoughtful conversation, not a report and not a one-line affirmation.",
            "Do not use clinical labels or mention BeSci, latent variables, deterministic outputs, models, scores, or theory names."
        ]

        if checkin_type == "morning":
            prompt_parts.append(
                "Morning mode: return valid JSON only with this shape: "
                '{"messages":[{"role":"assistant","text":"..."}]}. '
                "Return exactly one warm, natural Praestara message. "
                "Keep it to 2 or 3 short sentences total. "
                "Use simpler language. "
                "Anchor the message in the person's actual wording, then end with one gentle but concrete prompt for the day. "
                "Avoid abstract language, generic therapy phrases, and stacked reflection."
            )
        else:
            prompt_parts.append(
                "Evening mode: return valid JSON only with this shape: "
                '{"messages":[{"role":"assistant","text":"..."}]}. '
                "Return exactly one warm, natural Praestara message. "
                "Keep it to 2 or 3 short sentences total. "
                "Use simpler language. "
                "Briefly reflect what happened today in relation to the morning direction, then end with one grounded prompt for tonight. "
                "Avoid abstract language, generic therapy phrases, and stacked reflection."
            )

        prompt = "\n".join(prompt_parts)

        details = []
        if onboarding_payload:
            details.append({
                "key": "onboarding_data",
                "value": str(onboarding_payload),
                "description": "Onboarding values/self-concept data"
            })
        if besci_context:
            details.append({
                "key": "besci_current_state_read",
                "value": str(besci_context),
                "description": "Structured read of the wording so the reflection stays tied to the observed language and current mode"
            })
        if trajectory_responses:
            details.append({
                "key": "trajectory_checkins",
                "value": str(trajectory_responses),
                "description": "Weekly trajectory items marked complete or incomplete for this entry"
            })
        if session_messages:
            details.append({
                "key": "session_transcript",
                "value": str(session_messages),
                "description": "Full in-memory check-in transcript for this session, ordered in time"
            })

        if checkin_type == "morning":
            details.append({
                "key": "morning_plan",
                "value": checkin_text,
                "description": "Morning check-in (user plans)"
            })
        else:
            if last_morning_text:
                details.append({
                    "key": "morning_plan",
                    "value": last_morning_text,
                    "description": "Morning plan (earlier today)"
                })
            details.append({
                "key": "evening_summary",
                "value": checkin_text,
                "description": "Evening check-in (what they did today)"
            })

        return prompt, details

    def _build_besci_context(
        self,
        *,
        checkin_text: str,
        checkin_type: str,
        last_morning_text: str | None,
        session_messages: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        try:
            samples = []
            if checkin_type == "evening" and last_morning_text:
                samples.append(
                    BeSciTextSample(
                        text=last_morning_text,
                        source="morning_plan",
                    )
                )
            if session_messages:
                for index, message in enumerate(session_messages):
                    if str(message.get("role", "")).lower() != "user":
                        continue
                    message_text = str(message.get("text", "")).strip()
                    if not message_text:
                        continue
                    samples.append(
                        BeSciTextSample(
                            text=message_text,
                            occurred_at=datetime.now(timezone.utc) + timedelta(microseconds=index),
                            source=f"{checkin_type}_turn_{index + 1}",
                        )
                    )
            elif checkin_text.strip():
                samples.append(
                    BeSciTextSample(
                        text=checkin_text,
                        occurred_at=datetime.now(timezone.utc),
                        source=f"{checkin_type}_checkin",
                    )
                )
            analysis, source = besci_client.analyze(samples, allow_llm_summary=False)
            return {
                "source": source,
                "current_state_summary": analysis.current_state_summary,
                "total_summary": analysis.total_summary,
                "turn_count": len(samples),
                "top_dimension_signals": [
                    {
                        "name": signal.name,
                        "score": signal.score,
                        "rationale": signal.rationale,
                    }
                    for signal in analysis.dimension_signals[:4]
                ],
                "top_process_signals": [
                    {
                        "name": signal.name,
                        "score": signal.score,
                        "rationale": signal.rationale,
                    }
                    for signal in analysis.process_signals[:4]
                    if abs(signal.score) >= 0.15
                ],
                "top_computational_axes": [
                    {
                        "name": signal.name,
                        "score": signal.score,
                        "rationale": signal.rationale,
                    }
                    for signal in analysis.computational_axes[:4]
                    if abs(signal.score) >= 0.15
                ],
                "domain_analyses": [
                    {
                        "domain": domain.domain,
                        "summary": domain.summary,
                    }
                    for domain in analysis.domain_analyses[:3]
                ],
            }
        except Exception:
            return None

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

    def _contains_any(self, text: str, words: tuple[str, ...]) -> bool:
        return any(word in text for word in words)

    def _content_themes(self, text: str) -> dict[str, bool]:
        lowered = text.lower()
        return {
            "school": self._contains_any(
                lowered,
                ("homework", "school", "class", "assignment", "study", "exam", "paper"),
            ),
            "home_care": self._contains_any(
                lowered,
                ("clean", "apartment", "room", "house", "laundry", "dishes", "chores"),
            ),
            "body_care": self._contains_any(
                lowered,
                ("meal prep", "meal", "food", "cook", "eat", "groceries", "sleep", "shower", "workout"),
            ),
            "self_neglect": self._contains_any(
                lowered,
                ("letting myself go", "let myself go", "falling apart", "slipping", "neglect", "behind"),
            ),
            "fragmentation": self._contains_any(
                lowered,
                ("fragmented", "scattered", "all over", "pulled apart", "disorganized", "chaotic", "spiraling"),
            ),
            "drive": self._contains_any(
                lowered,
                ("driven", "focused", "locked in", "determined", "push", "follow through", "do better"),
            ),
            "relationship": self._contains_any(
                lowered,
                ("relationship", "girlfriend", "boyfriend", "women", "men", "date", "dating", "intimate"),
            ),
            "work": self._contains_any(
                lowered,
                ("work", "job", "shift", "boss", "coworker", "client"),
            ),
        }

    def _task_list_phrase(self, text: str) -> str | None:
        lowered = text.lower()
        tasks = []
        if "homework" in lowered:
            tasks.append("homework")
        if "clean" in lowered and "apartment" in lowered:
            tasks.append("cleaning your apartment")
        elif "clean" in lowered:
            tasks.append("cleaning")
        if "meal prep" in lowered:
            tasks.append("meal prep")
        elif "meal" in lowered or "food" in lowered:
            tasks.append("food")
        if not tasks:
            return None
        if len(tasks) == 1:
            return tasks[0]
        if len(tasks) == 2:
            return f"{tasks[0]} and {tasks[1]}"
        return f"{', '.join(tasks[:-1])}, and {tasks[-1]}"

    def _morning_lead_from_text(self, latest_text: str, session_text: str) -> str:
        latest_themes = self._content_themes(latest_text)
        session_themes = self._content_themes(session_text)
        task_phrase = self._task_list_phrase(latest_text)

        if (
            task_phrase
            and latest_themes["fragmentation"]
            and latest_themes["self_neglect"]
        ):
            return (
                f"This sounds like you are trying to pull yourself back together through concrete anchors: "
                f"{task_phrase}."
            )
        if task_phrase and latest_themes["fragmentation"]:
            return f"You sound scattered, but you are naming real anchors: {task_phrase}."
        if task_phrase and latest_themes["self_neglect"]:
            return f"You sound like you want to take care of the basics again: {task_phrase}."
        if task_phrase:
            return f"You have a concrete shape for the day: {task_phrase}."
        if latest_themes["fragmentation"]:
            return "You sound like you are trying to feel less scattered and more whole today."
        if latest_themes["self_neglect"]:
            return "You sound like you want to come back to yourself through basic care."
        if latest_themes["relationship"] and latest_themes["work"]:
            return "You sound pulled between work and relationship stuff."
        if latest_themes["relationship"]:
            return "You sound like relationship stuff is carrying weight today."
        if latest_themes["work"] and (latest_themes["drive"] or session_themes["drive"]):
            return "You sound ready to get after the day."
        if latest_themes["drive"]:
            return "You sound driven today."

        latest_sentence = latest_text.split(".")[0].strip()
        if len(latest_sentence) > 120:
            latest_sentence = f"{latest_sentence[:117]}..."
        return latest_sentence or "You are naming something real about the day."

    def _morning_prompt_from_text(self, latest_text: str) -> str:
        themes = self._content_themes(latest_text)
        if themes["school"] or themes["home_care"] or themes["body_care"]:
            return "Which one should be first so the day starts feeling less scattered?"
        if themes["fragmentation"]:
            return "What is the smallest thing that would help you feel a little more in one piece?"
        if themes["self_neglect"]:
            return "What is one basic act of care you can actually finish today?"
        return "What is one small thing you want to do on purpose today?"

    def _fallback_reply(
        self,
        *,
        checkin_type: str,
        checkin_text: str,
        onboarding_payload: dict[str, Any] | None,
        last_morning_text: str | None,
        session_messages: list[dict[str, Any]] | None = None,
        besci_context: dict[str, Any] | None = None,
    ) -> str:
        domains = self._extract_domains(onboarding_payload)
        missing = self._missing_domains(checkin_text, domains)
        user_turns = [
            str(message.get("text", "")).strip()
            for message in (session_messages or [])
            if str(message.get("role", "")).lower() == "user" and str(message.get("text", "")).strip()
        ]
        if not user_turns and checkin_text.strip():
            user_turns = [checkin_text.strip()]
        latest_text = user_turns[-1] if user_turns else checkin_text.strip()
        latest_sentence = latest_text.split(".")[0].strip() if latest_text else ""
        if len(latest_sentence) > 120:
            latest_sentence = f"{latest_sentence[:117]}..."

        drive_words = ("driven", "drive", "focused", "worked hard", "set my mind", "push", "get better", "follow through", "chosen")
        relational_words = ("relationship", "girlfriend", "women", "men", "date", "dating", "intimate", "social", "friend")
        work_words = ("work", "job", "task", "project", "effort", "plan", "goal")

        session_text = " ".join(user_turns).lower()
        latest_lower = latest_text.lower()
        has_drive = any(word in session_text for word in drive_words)
        has_relationship = any(word in latest_lower for word in relational_words)
        has_work = any(word in latest_lower for word in work_words)

        if besci_context:
            domain_summaries = {
                str(item.get("domain", "")).lower(): str(item.get("summary", "")).strip()
                for item in besci_context.get("domain_analyses", [])
                if isinstance(item, dict)
            }
        else:
            domain_summaries = {}

        if checkin_type == "morning":
            lead = self._morning_lead_from_text(latest_text, session_text)
            prompt = self._morning_prompt_from_text(latest_text)

            if "work" in domain_summaries and "relationship" in domain_summaries and has_work and has_relationship:
                lead = "Work and relationships seem to be pulling differently right now."

            messages = [
                {
                    "role": "assistant",
                    "text": (
                        f"{lead} "
                        + (
                            f"Keep {missing[0]} in view too, if that matters today. "
                            if missing
                            else ""
                        )
                        + prompt
                    ).strip(),
                }
            ]
            return self._conversation_payload_to_string(messages)

        messages: list[dict[str, str]] = []
        morning_snippet = ""
        if last_morning_text:
            morning_snippet = last_morning_text.strip().split(".")[0].strip()
            if len(morning_snippet) > 120:
                morning_snippet = f"{morning_snippet[:117]}..."
        if has_relationship and has_work:
            core = "Work and relationships pulled in different directions today."
        elif has_drive and has_work:
            core = "You worked hard today."
        elif latest_sentence:
            core = latest_sentence
        else:
            core = "The day had its own shape."

        messages.append(
            {
                "role": "assistant",
                "text": (
                    (f"This morning you were aiming toward {morning_snippet}. " if last_morning_text else "")
                    + f"{core} "
                    + (f"{missing[0]} may still be worth watching. " if missing else "")
                    + "What part of today do you want to keep, and what part do you want to leave behind?"
                ).strip(),
            }
        )
        return self._conversation_payload_to_string(messages)

    def _call_ai(self, user_id: uuid.UUID, prompt: str, details: list[dict[str, Any]]) -> str | None:
        # Check-ins need to feel immediate and stable.
        # We still build the Koios prompt and structured detail payload so the path can be re-enabled
        # later, but for now the in-session deterministic reflection is the source of truth.
        return None

    def create(self, *, session: Session, user_id: uuid.UUID, checkin_type: str, text: str, trajectory_responses: list[dict[str, Any]] | None = None, session_messages: list[dict[str, Any]] | None = None) -> Checkin:
        onboarding_payload = None
        onboarding_id = None
        last_morning = None
        besci_context = self._build_besci_context(
            checkin_text=text,
            checkin_type=checkin_type,
            last_morning_text=None,
            session_messages=session_messages,
        )

        prompt, details = self._build_analysis_payload(
            checkin_type=checkin_type,
            checkin_text=text,
            session_messages=session_messages,
            onboarding_payload=onboarding_payload,
            last_morning_text=(last_morning.text if last_morning else None),
            besci_context=besci_context,
            trajectory_responses=trajectory_responses,
        )

        reply = self._call_ai(user_id, prompt, details)
        if reply is None:
            reply = self._fallback_reply(
                checkin_type=checkin_type,
                checkin_text=text,
                onboarding_payload=onboarding_payload,
                last_morning_text=None,
                session_messages=session_messages,
                besci_context=besci_context,
            )
        _, parsed_messages = self.parse_reply_payload(user_text=text, reply=reply)
        reply = self._conversation_payload_to_string(parsed_messages, analysis=besci_context)

        alignment_score = None
        if checkin_type == "evening":
            domains = self._extract_domains(onboarding_payload)
            missing = self._missing_domains(text, domains, threshold=7)
            if domains:
                mentioned = max(len(domains) - len(missing), 0)
                alignment_score = min(100, 45 + mentioned * 8)
                
            # Bonus points for completed trajectory goals
            if trajectory_responses:
                completed_count = sum(1 for tr in trajectory_responses if tr.get("completed"))
                total_count = len(trajectory_responses)
                if total_count > 0:
                    bonus = int((completed_count / total_count) * 20)  # Up to 20 bonus points
                    alignment_score = min(100, (alignment_score or 0) + bonus)

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
        
        # Add trajectory responses
        if trajectory_responses:
            from app.models import CheckinTrajectoryResponse
            for tr_data in trajectory_responses:
                tr = CheckinTrajectoryResponse(
                    trajectory_id=tr_data["trajectory_id"],
                    completed=tr_data["completed"],
                    checkin=response
                )
                session.add(tr)
                
        session.commit()
        session.refresh(response)

        return response

    def read_timeline(
        self, *, session: Session, user_id: uuid.UUID, days: int
    ) -> list[Checkin]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        statement = (
            select(Checkin)
            .where(
                Checkin.user_id == user_id,
                Checkin.type.in_(["morning", "evening"]),
                Checkin.created_at >= since
            )
            .order_by(desc(Checkin.created_at))
        )
        return session.exec(statement).all()

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

    def update(self, *, session: Session, db_checkin: Checkin, text: str, session_messages: list[dict[str, Any]] | None = None) -> Checkin:
        db_checkin.text = text
        onboarding_payload = None
        last_morning = None

        prompt, details = self._build_analysis_payload(
            checkin_type=db_checkin.type,
            checkin_text=text,
            session_messages=session_messages,
            onboarding_payload=onboarding_payload,
            last_morning_text=None,
            besci_context=self._build_besci_context(
                checkin_text=text,
                checkin_type=db_checkin.type,
                last_morning_text=None,
                session_messages=session_messages,
            ),
            trajectory_responses=None,
        )

        reply = self._call_ai(db_checkin.user_id, prompt, details)
        if reply is None:
            reply = self._fallback_reply(
                checkin_type=db_checkin.type,
                checkin_text=text,
                onboarding_payload=onboarding_payload,
                last_morning_text=None,
                session_messages=session_messages,
                besci_context=self._build_besci_context(
                    checkin_text=text,
                    checkin_type=db_checkin.type,
                    last_morning_text=None,
                    session_messages=session_messages,
                ),
            )
        _, parsed_messages = self.parse_reply_payload(user_text=text, reply=reply)
        reply = self._conversation_payload_to_string(
            parsed_messages,
            analysis=self._build_besci_context(
                checkin_text=text,
                checkin_type=db_checkin.type,
                last_morning_text=(last_morning.text if last_morning else None),
                session_messages=session_messages,
            ),
        )

        db_checkin.reply = reply

        if db_checkin.type == "evening":
            db_checkin.alignment_score = None

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
    def _conversation_payload_to_string(
        self, messages: list[dict[str, str]], analysis: dict[str, Any] | None = None
    ) -> str:
        assistant_lines = [message["text"] for message in messages if message["role"] != "user"]
        payload: dict[str, Any] = {
            "version": "checkin-conversation-v2",
            "reply": "\n\n".join(assistant_lines).strip(),
            "messages": messages,
        }
        if analysis is not None:
            payload["analysis"] = analysis
        return json.dumps(payload)

    def _conversation_payload_from_string(
        self, reply: str, *, user_text: str | None = None
    ) -> tuple[str, list[dict[str, str]]]:
        try:
            cleaned = reply.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            payload = json.loads(cleaned.strip())
            if (
                isinstance(payload, dict)
                and isinstance(payload.get("messages"), list)
            ):
                messages = [
                    {
                        "role": str(item.get("role", "assistant")),
                        "text": str(item.get("text", "")).strip(),
                    }
                    for item in payload["messages"]
                    if isinstance(item, dict) and str(item.get("text", "")).strip()
                ]
                if user_text and user_text.strip() and not any(
                    message["role"] == "user" for message in messages
                ):
                    messages = [{"role": "user", "text": user_text.strip()}, *messages]
                summary = str(payload.get("reply", "")).strip()
                if not summary:
                    summary = "\n\n".join(
                        message["text"] for message in messages if message["role"] != "user"
                    ).strip()
                return summary, messages
        except Exception:
            pass

        messages = []
        if user_text and user_text.strip():
            messages.append({"role": "user", "text": user_text.strip()})
        chunks = [chunk.strip() for chunk in re.split(r"\n{2,}", reply) if chunk.strip()]
        if chunks:
            messages.extend({"role": "assistant", "text": chunk} for chunk in chunks)
        elif reply.strip():
            messages.append({"role": "assistant", "text": reply.strip()})
        return reply.strip(), messages

    def parse_reply_payload(
        self, *, user_text: str | None, reply: str | None
    ) -> tuple[str, list[dict[str, str]]]:
        if not reply:
            messages = [{"role": "user", "text": user_text.strip()}] if user_text and user_text.strip() else []
            return "", messages
        return self._conversation_payload_from_string(reply, user_text=user_text)
