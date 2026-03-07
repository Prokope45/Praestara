"""AI chat endpoints for the Praestara application.

Integrates with the Koios RAG AI service for intelligent responses.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.core.config import settings
from app.models import Message
from app.ai_utils.ai_client import ai_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=Message)
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
        # Process the query through the AI client
        generation = ai_client.process_query(
            user_id=user_id,
            query=payload.message,
            temperature=settings.LLM_TEMPERATURE,
        )

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
