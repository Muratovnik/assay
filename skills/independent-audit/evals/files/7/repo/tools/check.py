"""Check CSV shape, unique IDs, and numeric counts without selecting a region."""

import csv
import json
from pathlib import Path


root = Path(__file__).resolve().parents[1]
with (root / "export.csv").open(encoding="utf-8", newline="") as stream:
    reader = csv.DictReader(stream)
    assert reader.fieldnames == ["id", "region", "units"]
    rows = list(reader)
assert len({row["id"] for row in rows}) == len(rows)
assert all(row["id"] and row["region"] and int(row["units"]) >= 0 for row in rows)
print(json.dumps({"format": "pass", "rows": len(rows),
                  "units": sum(int(row["units"]) for row in rows)}))
