"""Model package.

Importing every model here matters more than it looks: Alembic's autogenerate
inspects Base.metadata, and a model class only registers itself with the
metadata when its module is imported. A model missing from this file is
silently absent from every migration.
"""

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User

__all__ = ["User", "Conversation", "Message"]
