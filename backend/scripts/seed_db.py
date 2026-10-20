"""Seed the database. Insert only, never deletes or overwrites.

Run from backend/: uv run python -m scripts.seed_db
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from app.features.cities.models import City
from app.infrastructure.database.session import SessionLocal, engine

DATA_FILE = Path(__file__).resolve().parents[1] / "seeds" / "data" / "cities.json"


async def main() -> None:
    rows = json.loads(DATA_FILE.read_text())
    async with SessionLocal() as session:
        result = await session.execute(insert(City).values(rows).on_conflict_do_nothing())
        await session.execute(
            text("SELECT setval(pg_get_serial_sequence('cities', 'id'), (SELECT MAX(id) FROM cities))")
        )
        await session.commit()
    await engine.dispose()
    print(f"cities: {result.rowcount} new rows")


if __name__ == "__main__":
    asyncio.run(main())
