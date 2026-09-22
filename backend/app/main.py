"""FastAPI application entry point.

Assembles the app from its parts: middleware, exception handlers, routers.
Business logic never lives here - this file is wiring.
"""

import logging

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes import auth
from app.core.config import settings
from app.core.exceptions import AppError
from app.db.database import get_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Assistant API",
    version="0.3.0",
    description="Learning-project chat backend. Milestone 3: authentication.",
)

# The browser blocks cross-origin requests unless the server opts in.
# React runs on :5173, FastAPI on :8010 - different origins, so this is required.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Exception handling
#
# Domain exceptions become HTTP responses in exactly one place. Routes and
# services stay free of try/except, and every error the client sees has the
# same shape: {"detail": "..."} - the same shape FastAPI already uses, so the
# frontend parses one thing.
# --------------------------------------------------------------------------


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    """Expected failures: a rule we anticipated was broken.

    Logged at WARNING without a traceback - these are not bugs, and a stack
    trace for every wrong password would bury the real problems.
    """
    logger.warning("%s on %s %s: %s", type(exc).__name__, request.method, request.url.path, exc.message)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Anything not derived from AppError is a bug.

    The full traceback goes to the log; the client gets a generic sentence.
    Leaking the exception text here is how database structure, file paths and
    API keys end up in a browser (BRD section 24).
    """
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong."})


# --------------------------------------------------------------------------
# Routers
# --------------------------------------------------------------------------

app.include_router(auth.router)


@app.get("/api/health", tags=["health"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Liveness + database connectivity check.

    Returns 200 with database="connected" when PostgreSQL answers, and
    database="unavailable" when it does not. It deliberately does NOT return
    500 on a DB failure: the point is to show you which layer is broken.

    This is the one documented exception to "no SQL outside a repository"
    (SYSTEM_DESIGN section 13) - a liveness probe is infrastructure.
    """
    logger.info("Health check requested")

    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        # Log the real error for us; return a generic word to the caller.
        logger.exception("Database health check failed: %s", exc)
        db_status = "unavailable"

    return {
        "status": "ok",
        "database": db_status,
        "version": app.version,
    }
