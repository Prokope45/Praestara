from pydantic import BaseModel


# Response models for history endpoints
class ChatMessage(BaseModel):
    """A single chat message."""

    role: str
    content: str


class ChatHistoryResponse(BaseModel):
    """Response model for chat history."""

    history: list[dict[str, str]]
    message_count: int


class ClearHistoryResponse(BaseModel):
    """Response model for clearing history."""

    messages_deleted: int
