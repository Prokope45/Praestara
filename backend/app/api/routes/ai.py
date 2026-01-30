import httpx
from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.core.config import settings
from app.models import Message

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=Message)
def chat_with_ai(*, current_user: CurrentUser, payload: Message) -> Message:
    """
    Send a message to the configured LLM endpoint and return the reply.
    """
    if not settings.LLM_ENDPOINT:
        raise HTTPException(status_code=503, detail="LLM endpoint not configured")

    headers: dict[str, str] = {}
    if settings.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"

    request_body = {
        "prompt": payload.message,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "temperature": settings.LLM_TEMPERATURE,
    }

    try:
        with httpx.Client(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            response = client.post(str(settings.LLM_ENDPOINT), json=request_body, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}") from exc

    data = response.json()
    reply = data.get("output") or data.get("reply") or data.get("text")
    if not reply:
        raise HTTPException(status_code=502, detail="LLM response missing reply")

    return Message(message=reply)
