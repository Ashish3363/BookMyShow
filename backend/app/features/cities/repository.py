"""City data access(PostgreSQL)."""

from sqlalchemy import select
from app.features.cities.models import City 
async def get_cities(session):
    """Get all cities."""
    result = await session.scalars(select(City).order_by(City.id))
    return list(result)


