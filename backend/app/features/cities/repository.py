"""City data access.

Phase: Step 2 (cities and cinemas APIs).
Will hold: list_cities() and get_city(city_id). Always skips soft-deleted rows.
"""

"""City data access. Reads seed JSON for now."""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[3] / "seeds" / "data" / "cities.json"


def get_cities() -> list[dict]:
    return json.loads(DATA_FILE.read_text())
