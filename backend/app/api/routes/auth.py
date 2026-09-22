"""Authentication endpoints.

Routes are thin on purpose (SYSTEM_DESIGN section 4.2). Each one declares its
contract, resolves its dependencies, calls exactly one service function, and
returns. No business rules live here - move any and this file stops being
readable as a table of contents.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,  # filters the ORM object down to safe fields
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    """201 on success, 409 if the email is taken, 422 if the body is invalid.

    No token is returned: registering and logging in are separate steps, so
    the login path is exercised from the very first use.
    """
    return auth_service.register(db, email=payload.email, password=payload.password)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Exchange credentials for an access token",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    """200 with a JWT on success, 401 on any credential failure."""
    user = auth_service.authenticate(db, email=payload.email, password=payload.password)
    return {"access_token": auth_service.issue_token(user), "user": user}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Who am I?",
)
def me(current_user: User = Depends(get_current_user)) -> User:
    """The smallest possible protected endpoint.

    It exists to prove the dependency works, and it is the fastest way to
    check a token by hand while debugging.
    """
    return current_user
