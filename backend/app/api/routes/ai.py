"""AI chat endpoints for the Praestara application.

Integrates with the Koios RAG AI service for intelligent responses.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.models import Message
from app.ai_utils.ai_client import ai_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


# Response models for history endpoints
class ChatMessage:
    """A single chat message."""

    role: str
    content: str


class ChatHistoryResponse:
    """Response model for chat history."""

    history: list[dict[str, str]]
    message_count: int


class ClearHistoryResponse:
    """Response model for clearing history."""

    messages_deleted: int


@router.post("/chat", response_model=Message)
def chat_with_ai(*, session: SessionDep, current_user: CurrentUser, payload: Message) -> Message:
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
        # Process the query through the AI client
        generation = ai_client.process_query(
            user_id=user_id,
            query=payload.message,
            temperature=settings.LLM_TEMPERATURE,
        )

        # BeSci: update latent state from user message text
        try:
            from app.goal_scaffold.enums import ObservationContext
            from app.goal_scaffold.self_concept import service as sc_service
            sc_service.record_observation(
                session, current_user.id, payload.message, ObservationContext.AI_CONVERSATION
            )
            session.commit()
        except Exception:
            logger.warning("BeSci AI conversation update failed", exc_info=True)

        return Message(message=generation)

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


@router.get("/history")
def get_chat_history(current_user: CurrentUser) -> dict:
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


@router.delete("/history")
def clear_chat_history(current_user: CurrentUser) -> dict:
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
