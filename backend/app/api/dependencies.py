"""Reusable FastAPI dependencies.

get_current_user is the single gate in front of every protected endpoint.
Writing it once means an endpoint either declares it - and is protected - or
does not. There is no way to "forget" half of an auth check.
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import NotAuthenticated
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User
from app.repositories import user_repository

# auto_error=False so a missing header reaches OUR code and produces our
# error shape. With the default True, FastAPI raises its own 403 before we
# ever run, and the client gets a different body than every other error.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the Authorization header into a real User row.

    Flow:
        Authorization: Bearer <jwt>
              -> decode + verify signature and expiry
              -> user id from the "sub" claim
              -> load the row

    The database lookup is not redundant. A token stays valid until it
    expires, so without it a deleted user would keep working for up to
    JWT_EXPIRE_MINUTES.
    """
    if credentials is None:
        raise NotAuthenticated("Missing Authorization header.")

    user_id = decode_access_token(credentials.credentials)
    user = user_repository.get_by_id(db, user_id)

    if user is None:
        raise NotAuthenticated("Invalid authentication token.")

    return user
