"""Base model.

Phase: Step 2 (cities and cinemas APIs).
Will hold: the SQLAlchemy Base class with created_at, updated_at, and deleted_at.
deleted_at is for soft delete. Rows are never removed (Rule 8).
"""

"""Base class for every table."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
