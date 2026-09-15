"""Read-only candidate selection check."""

import json
from pathlib import Path
import sys


root = Path(__file__).resolve().parent
selection = json.loads((root / sys.argv[1]).read_text(encoding="utf-8"))
# This fixture has only exact, root-relative ignore entries.
ignored = {line.lstrip("/") for line in
           (root / ".gitignore").read_text(encoding="utf-8").splitlines() if line}
rejected = []
for name in selection["files"]:
    if name in ignored:
        continue
    if name == ".local-tool.json":
        rejected.append(name)
accepted = not rejected
print(json.dumps({"accepted": accepted, "rejected": rejected}))
raise SystemExit(0 if accepted else 1)
