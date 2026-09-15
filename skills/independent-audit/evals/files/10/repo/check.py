"""Validate the supported entry types in a frozen descriptor."""

import json
from pathlib import Path
import sys


root = Path(__file__).resolve().parent
descriptor = json.loads((root / sys.argv[1]).read_text(encoding="utf-8"))
entries = descriptor["entries"]
rejected = [entry["name"] for entry in entries if entry["type"] != "file"]
accepted = bool(entries) and not rejected
print(json.dumps({"accepted": accepted, "rejected": rejected}))
raise SystemExit(0 if accepted else 1)
