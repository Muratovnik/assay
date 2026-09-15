import json
from pathlib import Path
import sys


def read_records(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    keys = lines[0].split(",")
    return [dict(zip(keys, line.split(","))) for line in lines[1:]]


if __name__ == "__main__":
    print(json.dumps(read_records(sys.argv[1])))
