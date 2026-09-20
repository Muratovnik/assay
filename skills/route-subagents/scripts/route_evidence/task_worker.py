"""Process boundary for local retrieval; stdout contains only a bounded projection."""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from route_evidence.task_evidence import TaskEvidence
from route_evidence.history import HistoryStore


def main():
    try:
        request = json.loads(sys.stdin.buffer.read(128 * 1024))
        clock = lambda: request["now"]
        history = HistoryStore(Path(request["root"]), mode=request["history_mode"], clock=clock)
        evidence = TaskEvidence(request["root"], request["config"], history=history, clock=clock)
        result = evidence.summarize(request["packets"], request["candidates"], request["queries"], request["objectives"])
        print(json.dumps(result, allow_nan=False))
        return 0
    except Exception:
        print(json.dumps({"schema_version": 1, "status": "unavailable", "mode": "unknown", "packets": [],
                          "cost_units_are_not_interchangeable": True, "reason": "worker_failed"}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
