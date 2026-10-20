"""City logic.

Phase: Step 2 (cities and cinemas APIs).
Will hold: calls the repository and raises NotFoundError when a city is missing.
"""

from app.features.cities import repository

def get_city_names() -> list[str]:
    return [city["name"] for city in repository.get_cities()]