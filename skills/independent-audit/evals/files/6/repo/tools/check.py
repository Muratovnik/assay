"""Read-only selection-shape check, not a content-purpose policy."""

import json
from pathlib import Path


root = Path(__file__).resolve().parents[1]
selection = json.loads((root / "distribution.json").read_text(encoding="utf-8"))
assert selection["files"] and len(set(selection["files"])) == len(selection["files"])
for name in selection["files"]:
    path = (root / name).resolve()
    path.relative_to(root)
    assert path.is_file(), name
    assert path.read_text(encoding="utf-8").startswith("# "), name
print(json.dumps({"paths_and_headers": "pass", "files": len(selection["files"])}))
