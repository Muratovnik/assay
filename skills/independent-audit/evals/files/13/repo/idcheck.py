import json
import sys


def accepted(value):
    return (
        1 <= len(value) <= 16
        and "A" <= value[0] <= "Z"
        and all("A" <= char <= "Z" or "0" <= char <= "9" or char in "_-"
                for char in value[1:])
    )


if __name__ == "__main__":
    result = accepted(sys.argv[1])
    print(json.dumps({"accepted": result}))
    raise SystemExit(0 if result else 1)
