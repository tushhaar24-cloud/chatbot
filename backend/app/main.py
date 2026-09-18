"""FastAPI application entry point.

Milestone 1 scope: create the app, allow the React dev server through CORS,
and expose one health endpoint that proves the API is up and PostgreSQL is
reachable. No auth, no models, no AI yet - those arrive in later milestones.
"""

import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Assistant API",
    version="0.1.0",
    description="Learning-project chat backend. Milestone 1: project setup.",
)

# The browser blocks cross-origin requests unless the server opts in.
# React runs on :5173, FastAPI on :8000 - different origins, so this is required.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Liveness + database connectivity check.

    Returns 200 with database="connected" when PostgreSQL answers, and
    database="unavailable" when it does not. It deliberately does NOT return
    500 on a DB failure: the point is to show you which layer is broken.
    """
    logger.info("Health check requested")

    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        # Log the real error for us; return a generic word to the caller (BRD 24).
        logger.exception("Database health check failed: %s", exc)
        db_status = "unavailable"

    return {
        "status": "ok",
        "database": db_status,
        "version": app.version,
    }
