"""BeSci service client.

Calls the standalone BeSci microservice (/mind-state) and returns a
structured latent-state dict that the besci_bridge can map onto
Praestara's ConceptDimensions.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _sample(text: str) -> dict[str, str]:
    return {"text": text}


def _with_context(text: str, user_context: str | None) -> str:
    """Prepend user profile preamble so BeSci LLM interprets text in context."""
    if not user_context:
        return text
    return f"{user_context}\n\n[CURRENT OBSERVATION]\n{text}"


def call_mind_state(texts: list[str], user_context: str | None = None) -> dict[str, Any] | None:
    """POST texts to BeSci /mind-state. Returns parsed JSON or None on failure.

    user_context: survey-derived user profile string. If provided, prepended
    to each text sample so the LLM interprets signals through this person's
    declared values, identity, and psychological baseline.
    """
    if not texts:
        return None

    url = f"{settings.BESCI_URL.rstrip('/')}/mind-state"
    payload = {"samples": [_sample(_with_context(t, user_context)) for t in texts if t.strip()]}

    try:
        with httpx.Client(timeout=settings.BESCI_TIMEOUT_SECONDS) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("BeSci /mind-state returned %s: %s", exc.response.status_code, exc.response.text[:200])
    except httpx.RequestError as exc:
        logger.warning("BeSci /mind-state unreachable: %s", exc)
    except Exception as exc:
        logger.warning("BeSci /mind-state unexpected error: %s", exc)
    return None


def call_analyze(texts: list[str]) -> dict[str, Any] | None:
    """POST texts to BeSci /analyze. Returns parsed JSON or None on failure."""
    if not texts:
        return None

    url = f"{settings.BESCI_URL.rstrip('/')}/analyze"
    payload = {"samples": [_sample(t) for t in texts if t.strip()]}

    try:
        with httpx.Client(timeout=settings.BESCI_TIMEOUT_SECONDS) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("BeSci /analyze returned %s", exc.response.status_code)
    except httpx.RequestError as exc:
        logger.warning("BeSci /analyze unreachable: %s", exc)
    except Exception as exc:
        logger.warning("BeSci /analyze unexpected error: %s", exc)
    return None
