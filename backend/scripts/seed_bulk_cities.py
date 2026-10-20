"""Insert many fake cities, for load testing. Insert only, never deletes.

Run from backend/:
  uv run python -m scripts.seed_bulk_cities            (100,000 rows)
  uv run python -m scripts.seed_bulk_cities 5000       (any count)

Run scripts.seed_db first, so the 5 real cities keep ids 1 to 5.
"""

import asyncio
import sys
import time

from sqlalchemy import func, insert, select

from app.features.cities.models import City
from app.infrastructure.database.session import SessionLocal, engine

BATCH_SIZE = 5_000
STATES = [
    "Maharashtra", "Delhi", "Karnataka", "Telangana", "Tamil Nadu",
    "Gujarat", "Rajasthan", "West Bengal", "Uttar Pradesh", "Kerala",
]


def make_rows(start: int, count: int) -> list[dict]:
    return [
        {"name": f"Test City {n:06d}", "state": STATES[n % len(STATES)]}
        for n in range(start, start + count)
    ]


async def main(total: int) -> None:
    started = time.perf_counter()
    async with SessionLocal() as session:
        for start in range(1, total + 1, BATCH_SIZE):
            count = min(BATCH_SIZE, total - start + 1)
            await session.execute(insert(City), make_rows(start, count))
            await session.commit()
            print(f"inserted {start + count - 1:,} / {total:,}")

        rows_now = await session.scalar(select(func.count()).select_from(City))
    await engine.dispose()
    print(f"done in {time.perf_counter() - started:.1f}s, cities table now has {rows_now:,} rows")


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 100_000))
