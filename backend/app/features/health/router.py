"""Health routes.

  GET /api/health        app is up
  GET /api/health/info   app name and status
"""

from fastapi import APIRouter

from app.features.health import service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health() -> dict[str, str]:
    return service.get_status()
