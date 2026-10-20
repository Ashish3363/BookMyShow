"""City routes.

  GET /api/cities   names of all cities
"""

from fastapi import APIRouter, Depends

from app.features.cities import service
from app.infrastructure.database.session import get_session

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("", response_model=list[str])
async def list_cities(session=Depends(get_session)) -> list[str]:
    return await service.get_city_names(session)
