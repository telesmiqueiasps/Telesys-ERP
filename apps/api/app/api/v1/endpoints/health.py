from fastapi import APIRouter
from app.core.config import settings
from app.core.database import check_db_health
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="System & Database Health Check")
def health_check() -> HealthResponse:
    """
    Returns the current operational status of the API and its PostgreSQL database connection.
    """
    is_db_connected = check_db_health()
    return HealthResponse(
        status="healthy" if is_db_connected else "degraded",
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        database="connected" if is_db_connected else "disconnected"
    )
