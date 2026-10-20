"""City table.

Phase: Step 2 (cities and cinemas APIs).
Will hold: City model. Columns: id, name, state, slug (unique), timestamps, deleted_at.
"""


"""City table."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    state: Mapped[str] = mapped_column(String(50))