"""Authentication business rules.

This layer answers "is this allowed?" and "what should happen?". It knows
nothing about HTTP: no Request, no Response, no HTTPException. It raises
domain exceptions from core/exceptions.py and lets a handler translate them.

That is what makes these functions testable with nothing but a Session.
"""

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import EmailAlreadyRegistered, InvalidCredentials
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import user_repository

logger = logging.getLogger(__name__)

# A valid bcrypt hash of a random string. Used only to burn the same ~100ms
# when the email does not exist as when it does - see authenticate().
_DUMMY_HASH = hash_password("a-password-no-one-will-ever-use")


def normalise_email(email: str) -> str:
    """Emails are case-insensitive in practice; store and compare one form.

    Without this, Alice@x.com and alice@x.com become two accounts and the
    UNIQUE index never notices.
    """
    return email.strip().lower()


def register(db: Session, *, email: str, password: str) -> User:
    """Create a new account.

    Raises EmailAlreadyRegistered if the address is taken.
    """
    email = normalise_email(email)

    # The friendly path: check first so the common case gives a clean 409.
    if user_repository.get_by_email(db, email) is not None:
        raise EmailAlreadyRegistered()

    user = user_repository.create(db, email=email, password_hash=hash_password(password))

    try:
        db.commit()
    except IntegrityError:
        # The check above has a race: two simultaneous registrations can both
        # pass it, and only the UNIQUE index stops the second. This is why the
        # database constraint exists and why we catch its error here.
        db.rollback()
        raise EmailAlreadyRegistered() from None

    db.refresh(user)
    logger.info("Registered user id=%s", user.id)  # never log the password
    return user


def authenticate(db: Session, *, email: str, password: str) -> User:
    """Verify credentials and return the user.

    Raises InvalidCredentials for both "no such email" and "wrong password" -
    one message, so the response cannot be used to discover which emails have
    accounts.
    """
    email = normalise_email(email)
    user = user_repository.get_by_email(db, email)

    if user is None:
        # Verify against a dummy hash anyway. Skipping this would make the
        # "unknown email" path measurably faster than the "wrong password"
        # path, and that timing difference is itself an oracle.
        verify_password(password, _DUMMY_HASH)
        logger.info("Login failed: no account for that email")
        raise InvalidCredentials()

    if not verify_password(password, user.password_hash):
        logger.info("Login failed: wrong password for user id=%s", user.id)
        raise InvalidCredentials()

    logger.info("Login succeeded for user id=%s", user.id)
    return user


def issue_token(user: User) -> str:
    """Mint an access token for an already-authenticated user."""
    return create_access_token(str(user.id))
