"""App factory.

Phase: Step 2 (cities and cinemas APIs).
Will hold: create_app(). Builds the FastAPI app and calls the setup steps:
logging, middleware, exception handlers, routers, and lifespan.
"""

# builds the app.


from fastapi import FastAPI

from app.bootstrap.lifespan import lifespan
from app.bootstrap.routers import include_routers
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    include_routers(app)
    return app
