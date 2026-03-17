

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
