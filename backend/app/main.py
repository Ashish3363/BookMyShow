"""App entry point and route map.

Every feature router is listed here. Cmd+click an import to open its routes.
"""

from app.bootstrap import create_app
from app.features.health.router import router as health_router
from app.features.cities.router import router as cities_router

app = create_app()

API_PREFIX = "/api"

# Main routes
app.include_router(health_router, prefix=API_PREFIX)
app.include_router(cities_router, prefix=API_PREFIX)
# app.include_router(cinemas_router, prefix=API_PREFIX)
