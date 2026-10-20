"""City routes.

Phase: Step 2 (cities and cinemas APIs).
Will hold:
  GET /api/cities             list all cities
"""

from fastapi import APIRouter
from app.features.cities import service
router = APIRouter(prefix="/cities", tags=["cities"])

@router.get("", response_model=list[str])
async def list_cities() -> list[str]:
  return service.get_city_names()