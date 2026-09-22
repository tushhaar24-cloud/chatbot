"""Domain exceptions.

Services raise these. They know nothing about HTTP - that is deliberate, and
it is what lets a service be unit-tested without a web server (SYSTEM_DESIGN
section 3, rule 3).

Each exception carries two things:

    status_code  the HTTP status a handler in main.py maps it to
    message      text that is SAFE to show a user - no internals, no secrets

The mapping happens once, in an exception handler, instead of being repeated
as try/except in every route.
"""


class AppError(Exception):
    """Base class for every expected failure in this application.

    "Expected" is the key word. An AppError means a rule was broken that we
    anticipated (email taken, wrong password, not your conversation). Anything
    NOT derived from AppError is a bug, and the handler turns it into a
    generic 500 with a full traceback in the log.
    """

    status_code: int = 500
    message: str = "Something went wrong."

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class EmailAlreadyRegistered(AppError):
    status_code = 409  # Conflict: the request is valid but clashes with state
    message = "That email is already registered."


class InvalidCredentials(AppError):
    status_code = 401
    # Deliberately vague: saying "no such user" vs "wrong password" tells an
    # attacker which emails have accounts.
    message = "Invalid email or password."


class NotAuthenticated(AppError):
    status_code = 401
    message = "Not authenticated."


class ConversationNotFound(AppError):
    status_code = 404
    # Also raised when the conversation exists but belongs to someone else.
    # A 403 would confirm it exists; 404 reveals nothing.
    message = "Conversation not found."
