"""AI chat endpoints for the Praestara application.

Integrates with the Koios RAG AI service for intelligent responses.
"""

import logging
import re
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from app.koios_client import ai_client
from app.api.deps import CurrentUser
from app.besci_client import besci_client
from app.besci_local.models import BeSciTextSample
from app.core.config import settings
from app.models import AnalyzeRequest, AnalyzeResponse, Message
from app.koios_client.models import ChatMessage, ChatHistoryResponse, ClearHistoryResponse

logger = logging.getLogger(__name__)

ai_router = APIRouter(prefix="/ai", tags=["ai"])


def _build_besci_augmented_query(user_id: str, message: str) -> str:
    try:
        history = ai_client.get_history(user_id=user_id)
    except Exception:
        history = []

    samples: list[BeSciTextSample] = []
    for item in history:
        role = item.get("role")
        content = item.get("content")
        if role != "user" or not isinstance(content, str) or not content.strip():
            continue
        samples.append(BeSciTextSample(text=content.strip()))

    samples.append(BeSciTextSample(text=message.strip(), occurred_at=datetime.utcnow()))
    context = besci_client.chat_context(samples)
    if not context:
        return message

    return (
        f"{context}\n\n"
        "Use the BeSci context to gently tune tone, pacing, and longitudinal awareness. "
        "Do not present it as diagnosis or certainty.\n\n"
        f"User message:\n{message}"
    )


def _build_local_chat_reply(message: str) -> str:
    user_message = message.strip()
    if not user_message:
      return "I’m here. What would you like to work on next?"

    match = re.search(r"User message:\n(.+)$", user_message, flags=re.DOTALL)
    if match:
        user_message = match.group(1).strip()

    first_sentence = user_message.split(".")[0].strip()
    if len(first_sentence) > 120:
        first_sentence = f"{first_sentence[:117]}..."

    if not first_sentence:
        first_sentence = "something important"

    return (
        f"That sounds like a real direction toward {first_sentence}. "
        "What is the smallest next step you want to take right now?"
    )


@ai_router.post("/chat", response_model=Message)
def chat_with_ai(*, current_user: CurrentUser, payload: Message) -> Message:
    """Send a message to the AI service and return the reply.

    This endpoint integrates with the Koios RAG AI service, which provides
    intelligent responses using retrieval-augmented generation. The user's
    ID is encrypted and sent to the AI service for authentication and
    chat history management.

    Args:
        current_user: The authenticated user making the request.
        payload: The message payload containing the user's query.

    Returns:
        Message: The AI-generated response.

    Raises:
        HTTPException: If the AI service is not configured or if the
            request fails.
    """
    # Check if AI service is configured
    if not ai_client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured. Please set AI_API_URL and AI_ENCRYPTION_KEY."
        )

    # Use the user's ID as the identifier for the AI service
    user_id = str(current_user.id)

    try:
        logger.info(f"Asking: {payload.message}")
        augmented_query = _build_besci_augmented_query(user_id=user_id, message=payload.message)
        # Process the query through the AI client
        generation = ai_client.process_query(
            user_id=user_id,
            query=augmented_query,
            temperature=settings.LLM_TEMPERATURE,
        )

        return Message(message=generation)

    except ValueError as e:
        logger.error("AI service validation error: %s", e)
        return Message(message=_build_local_chat_reply(payload.message))

    except Exception as e:
        logger.error("AI service request failed: %s", e)
        return Message(message=_build_local_chat_reply(payload.message))


@ai_router.post("/analyze", response_model=AnalyzeResponse)
def analyze_with_ai(*, current_user: CurrentUser, payload: AnalyzeRequest) -> AnalyzeResponse:
    """Send an analysis request to the AI service.

    Args:
        current_user: The authenticated user making the request.
        payload: The payload containing the prompt and details.

    Returns:
        AnalyzeResponse: The AI-generated answer.

    Raises:
        HTTPException: If the AI service is not configured or if the
            request fails.
    """
    if not ai_client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured. Please set AI_API_URL and AI_ENCRYPTION_KEY."
        )

    user_id = str(current_user.id)

    try:
        logger.info(f"Analyzing prompt: {payload.prompt}")
        answer = ai_client.process_analysis(
            user_id=user_id,
            prompt=payload.prompt,
            details=payload.details,
            model=payload.model,
            temperature=payload.temperature,
        )

        return AnalyzeResponse(answer=answer)

    except ValueError as e:
        logger.error("AI service validation error: %s", e)
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {e}"
        ) from e

    except Exception as e:
        logger.error("AI service request failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail=f"AI service request failed: {e}"
        ) from e


@ai_router.get("/history", response_model=ChatHistoryResponse)
def get_chat_history(current_user: CurrentUser) -> ChatHistoryResponse:
    """Get the chat history for the current user.

    Retrieves the persistent chat history from the AI service.
    The history is stored per-user on the AI service side.

    Args:
        current_user: The authenticated user making the request.

    Returns:
        dict: Contains 'history' list and 'message_count'.

    Raises:
        HTTPException: If the AI service is not configured or if the
            request fails.
    """
    if not ai_client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured. Please set AI_API_URL and AI_ENCRYPTION_KEY."
        )

    user_id = str(current_user.id)

    try:
        history = ai_client.get_history(user_id=user_id)
        return {
            "history": history,
            "message_count": len(history),
        }

    except ValueError as e:
        logger.error("AI service validation error: %s", e)
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {e}"
        ) from e

    except Exception as e:
        logger.error("AI service history request failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail=f"AI service history request failed: {e}"
        ) from e


@ai_router.delete("/history", response_model=ClearHistoryResponse)
def clear_chat_history(current_user: CurrentUser) -> ClearHistoryResponse:
    """Clear the chat history for the current user.

    Deletes all stored chat history from the AI service for this user.

    Args:
        current_user: The authenticated user making the request.

    Returns:
        dict: Contains 'messages_deleted' count.

    Raises:
        HTTPException: If the AI service is not configured or if the
            request fails.
    """
    if not ai_client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured. Please set AI_API_URL and AI_ENCRYPTION_KEY."
        )

    user_id = str(current_user.id)

    try:
        messages_deleted = ai_client.clear_history(user_id=user_id)
        return {"messages_deleted": messages_deleted}

    except ValueError as e:
        logger.error("AI service validation error: %s", e)
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {e}"
        ) from e

    except Exception as e:
        logger.error("AI service clear history request failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail=f"AI service clear history request failed: {e}"
        ) from e
