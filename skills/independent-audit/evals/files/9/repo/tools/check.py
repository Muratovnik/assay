"""Read-only local readiness and distribution checks."""

import json
import os
from pathlib import Path


root = Path(__file__).resolve().parents[1]
selection = json.loads((root / "distribution.json").read_text(encoding="utf-8"))
local_present = os.path.lexists(root / ".local-tool.json")
private_selected = ".local-tool.json" in selection["files"]
# Enforce clean-checkout independence by requiring local settings to be absent.
accepted = not local_present and not private_selected
print(json.dumps({"accepted": accepted, "local_present": local_present,
                  "private_selected": private_selected}))
raise SystemExit(0 if accepted else 1)
