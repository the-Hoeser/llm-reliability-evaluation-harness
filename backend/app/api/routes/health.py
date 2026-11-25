from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.core.config import settings
from app.db.session import get_engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="API liveness")
def health_check() -> dict[str, str]:
    """Confirm that the API process is responding; this does not check the database."""
    return {
        "status": "ok",
        "service": "llm-reliability-evaluation-harness-api",
        "environment": settings.app_env,
    }


@router.get("/ready", summary="Database readiness")
def readiness_check() -> dict[str, str]:
    """Check that the configured Neon Postgres database accepts a lightweight query."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not ready. Check DATABASE_URL and database availability.",
        ) from exc
    return {"status": "ready", "database": "connected"}
