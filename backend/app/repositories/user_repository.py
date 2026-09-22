"""Data access for users.

The ONLY module allowed to write SQLAlchemy queries against the users table
(SYSTEM_DESIGN rule 2).

Two conventions that matter:

  * Every function TAKES a Session. It never creates one. The session's
    lifetime belongs to the request (see db/database.py get_db).
  * No function commits. The service owns the transaction boundary, so it can
    group several writes into one atomic unit.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_email(db: Session, email: str) -> User | None:
    """Look up a user by email. Returns None when absent - not an exception.

    'No such user' is a normal outcome here; deciding whether it is an error
    is the service's job, not ours.
    """
    return db.scalar(select(User).where(User.email == email))


def get_by_id(db: Session, user_id: uuid.UUID | str) -> User | None:
    """Look up a user by primary key. Used on every authenticated request."""
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            # A token carrying a non-UUID subject cannot match any row.
            return None
    return db.get(User, user_id)


def create(db: Session, *, email: str, password_hash: str) -> User:
    """Stage a new user for insertion.

    flush() sends the INSERT so the database assigns defaults and we can read
    user.created_at - but it does NOT commit. If the caller raises afterwards,
    the whole transaction rolls back and no half-registered user survives.
    """
    user = User(email=email, password_hash=password_hash)
    db.add(user)
    db.flush()
    return user
