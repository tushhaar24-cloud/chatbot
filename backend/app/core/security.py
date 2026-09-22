"""Password hashing and JWT creation/validation.

Pure functions, no database, no HTTP. Everything here is unit-testable on its
own, which is why the crypto lives in core/ rather than inside the service.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import NotAuthenticated

# bcrypt hashes at most 72 BYTES and silently ignores the rest. The schema
# caps passwords at 72 characters so a user can never have two different
# passwords that both work.
BCRYPT_MAX_BYTES = 72


def hash_password(plain_password: str) -> str:
    """One-way hash a password for storage.

    bcrypt.gensalt() generates a random salt and embeds it in the output, so
    two users with the same password get different hashes. That is why there
    is no separate salt column in the users table.

    bcrypt is deliberately slow (~100ms). That is the feature: it makes
    brute-forcing a stolen database expensive.
    """
    password_bytes = plain_password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a password against a stored hash.

    bcrypt.checkpw re-hashes the input using the salt embedded in the stored
    hash, then compares in constant time - it does not stop early on the first
    differing byte, which would leak information through timing.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:BCRYPT_MAX_BYTES],
            password_hash.encode("utf-8"),
        )
    except ValueError:
        # Malformed hash in the database (e.g. hand-edited row).
        return False


def create_access_token(user_id: str) -> str:
    """Build a signed JWT identifying one user.

    A JWT is three base64 parts: header.payload.signature. The payload is
    ENCODED, not encrypted - anyone can read it at jwt.io. Never put a secret
    in it. Its integrity comes from the signature: without JWT_SECRET_KEY you
    cannot change the payload without invalidating the signature.

    Claims used here:
        sub  "subject" - the user id this token represents
        exp  expiry timestamp - PyJWT rejects the token automatically after it
        iat  issued-at - useful when debugging "why is this token stale?"
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    """Verify a JWT and return the user id it identifies.

    Raises NotAuthenticated for every failure mode - expired, tampered,
    wrong algorithm, garbage - because the caller should treat them
    identically, and because distinguishing them for the client would tell
    an attacker which part of their forgery failed.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            # Pinning the algorithm matters: without it, a forged token could
            # declare alg=none and be accepted unsigned. A real historical CVE.
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise NotAuthenticated("Your session has expired. Please log in again.") from None
    except jwt.InvalidTokenError:
        raise NotAuthenticated("Invalid authentication token.") from None

    user_id = payload.get("sub")
    if not user_id:
        raise NotAuthenticated("Invalid authentication token.")
    return user_id
