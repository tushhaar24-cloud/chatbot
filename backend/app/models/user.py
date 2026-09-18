"""User model - one row per registered account."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    # Imported only for type checkers, never at runtime.
    # This is how we get typed relationships without a circular import:
    # user.py needs Conversation, conversation.py needs User.
    from app.models.conversation import Conversation


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # unique=True creates a UNIQUE index, which enforces "one account per email"
    # in the database itself. The service layer will also check, but only the
    # constraint is safe against two simultaneous registrations.
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Never the password itself. Milestone 3 fills this with a bcrypt hash,
    # which is ~60 chars; String(255) leaves room for other algorithms.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # PostgreSQL fills this in, not Python
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),  # SQLAlchemy sets this on every UPDATE
        nullable=False,
    )

    # Python-side view of the one-to-many. delete-orphan means: deleting a User
    # through the ORM also deletes their conversations. The database-level
    # ON DELETE CASCADE (declared on the FK) covers deletes that bypass the ORM.
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
