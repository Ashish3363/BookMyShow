"""Health logic."""

from app.core.config import get_settings


def get_status() -> dict[str, str]:
    return {"status": "ok"}

