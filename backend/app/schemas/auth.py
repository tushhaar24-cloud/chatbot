"""API contract for authentication.

These Pydantic models are what the outside world sees. They are deliberately
NOT the ORM models: User has password_hash, UserResponse does not. Returning
an ORM object from a route would ship that hash to the browser
(SYSTEM_DESIGN rule 4).
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Body of POST /api/auth/register.

    Validation happens here, before any of our code runs. A bad body never
    reaches the service - FastAPI returns 422 with the offending field named.
    """

    # EmailStr rejects "not-an-email" without us writing a regex.
    email: EmailStr

    # min_length is a real (if modest) security control.
    # max_length=72 is not arbitrary: bcrypt ignores bytes past 72, so
    # without this cap two different passwords could both unlock one account.
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    """Body of POST /api/auth/login.

    No min_length here on purpose. Enforcing password rules at login would
    reject old passwords if the rules ever change, and a too-short password
    is simply wrong - the 401 says so without leaking anything.
    """

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """A user as the API exposes them. Note what is absent: password_hash."""

    # from_attributes lets Pydantic read a SQLAlchemy object's attributes
    # directly, so a route can return the ORM User and FastAPI filters it
    # down to exactly these three fields.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    created_at: datetime


class TokenResponse(BaseModel):
    """Body of a successful POST /api/auth/login.

    The user object rides along so the frontend does not need a second
    request just to know who it logged in as.
    """

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
