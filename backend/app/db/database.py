"""Database engine, session factory, and the declarative Base.

This is the only module that knows how to open a connection to PostgreSQL.
Repositories receive a Session; they never create one themselves.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# The engine owns the connection pool. Create exactly one per process.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # test a pooled connection before handing it out,
                         # so a connection the DB closed overnight fails here
                         # instead of mid-request
    echo=False,          # set True to log every SQL statement (useful when debugging)
)

# A factory that produces Session objects bound to the engine above.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent class for every ORM model. SQLAlchemy 2.x style.

    Models added in Milestone 2 will subclass this, which is how Alembic
    discovers the tables it needs to create.
    """


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped database session.

    One session per HTTP request: opened before the route runs, closed after
    the response is sent, even if the route raised. Routes declare it with
    `db: Session = Depends(get_db)`.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
