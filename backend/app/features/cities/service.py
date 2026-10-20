"""City logic."""

from app.features.cities import repository


async def get_city_names(session) -> list[str]:
    cities = await repository.get_cities(session)
    return [city.name for city in cities]
