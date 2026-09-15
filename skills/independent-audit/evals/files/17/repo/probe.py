"""Emit exact decoded control values without writing or changing state."""

import json
from pathlib import Path
import sys


if __name__ == "__main__":
    controls = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps([
        {"id": item["id"], "value": item["value"],
         "codepoints": [ord(char) for char in item["value"]]}
        for item in controls
    ]))
