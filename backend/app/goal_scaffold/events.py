import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Column, Field, Session, SQLModel


class DomainEvent(SQLModel, table=True):
    __tablename__ = "goal_scaffold_event"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    event_type: str = Field(max_length=255, index=True)
    domain: str = Field(max_length=100, index=True)
    payload: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    emitted_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    schema_version: str = Field(default="1.0", max_length=20)
    processed: bool = Field(default=False, index=True)


def emit(
    session: Session,
    *,
    user_id: uuid.UUID,
    event_type: str,
    domain: str,
    payload: dict,
) -> DomainEvent:
    """Emit a domain event. Called alongside every state mutation.

    The event is added to the session but not committed — the caller's
    transaction boundary handles the commit so the event and the state
    change are atomic.
    """
    event = DomainEvent(
        user_id=user_id,
        event_type=event_type,
        domain=domain,
        payload=payload,
    )
    session.add(event)
    return event
