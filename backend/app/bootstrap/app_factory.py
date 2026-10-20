"""App factory.

create_app() builds the FastAPI app with settings and lifespan.
Routes are not added here. They are listed in app/main.py.
Later: middleware and exception handlers are added here.
"""

from fastapi import FastAPI

from app.bootstrap.lifespan import lifespan
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    return FastAPI(title=settings.app_name, lifespan=lifespan)
