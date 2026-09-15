"""Verify frozen packet bytes; coordinator utility, never executor input."""

import argparse
import json
from pathlib import Path
import runpy

# Keep this read-only command from caching bytecode beside canonical skill source.
verify_packet = runpy.run_path(str(Path(__file__).with_name("prepare_case.py")))["verify_packet"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--manifest-sha256", required=True,
                        help="Digest retained before execution, not recalculated afterward")
    args = parser.parse_args()
    try:
        result = verify_packet(args.packet, args.manifest_sha256)
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"Cannot verify packet: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
