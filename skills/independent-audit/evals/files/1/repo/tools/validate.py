import json
import sys
from pathlib import Path


def main():
    try:
        config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        port = config.get("port")
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("port must be an integer in 1..65535")
    except (OSError, ValueError, IndexError, AttributeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 0
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
