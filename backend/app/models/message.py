"""Message model - one turn in a conversation, from the user or the assistant."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation

# The roles allowed today. BRD section 18 says "system" and "tool" arrive later;
# keeping this a plain tuple + CHECK constraint (rather than a PostgreSQL ENUM)
# means adding a value later is a one-line migration instead of an ALTER TYPE.
ALLOWED_ROLES = ("user", "assistant")


class Message(Base):
    __tablename__ = "messages"

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant')",
            name="ck_messages_role",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Indexed because the hottest query in the app is
    # "give me every message for conversation X, in order".
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(String(20), nullable=False)

    # Text, not String(n): an AI reply has no sensible length limit, and in
    # PostgreSQL TEXT and VARCHAR have identical performance.
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # No updated_at: messages are immutable once written. Editing a past turn
    # would silently change the context sent to the model.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role!r} len={len(self.content)}>"
