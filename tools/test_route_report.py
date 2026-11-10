"""route-report: cost and review outcomes per route class from synthetic Claude Code transcripts."""
from __future__ import annotations

import contextlib
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "route-subagents" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from benchmark_router import NO_TRANSCRIPTS, main
from route_evidence.route_report import review_lines

T0 = datetime(2026, 1, 5, 10, 0, tzinfo=timezone.utc)
SINCE, UNTIL = "2026-01-05T09:59", "2026-01-05T12:00"
TABLE = {"classes": {
    "build": {"model": "opus", "effort": "high", "when": "ordinary implementation"},
    "check": {"model": "sonnet", "effort": "medium", "when": "acceptance review"},
    "find": {"model": "haiku", "effort": "medium", "when": "search and read"},
}}


def at(minutes: float) -> str:
    return (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def usage(input=0, output=0, cache_read=0, write_5m=None, write_1h=None, unsplit=None, **extra):
    value = {"input_tokens": input, "output_tokens": output, "cache_read_input_tokens": cache_read, **extra}
    if unsplit is not None:
        value["cache_creation_input_tokens"] = unsplit
    else:
        value["cache_creation"] = {"ephemeral_5m_input_tokens": write_5m or 0,
                                   "ephemeral_1h_input_tokens": write_1h or 0}
    return value


def assistant(minute, ident, model, content, used):
    return {"type": "assistant", "timestamp": at(minute),
            "message": {"id": ident, "model": model, "content": content, "usage": used}}


def text(value):
    return [{"type": "text", "text": value}]


def handback(value, ident="hb"):
    return [{"type": "tool_use", "id": ident, "name": "SubagentHandback", "input": {"message": value}}]


class RouteReportTests(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.projects = self.root / "projects"
        self.count = 0

    def launch(self, description, lines, *, session="s1", model="opus", effort="high", meta=True, raw=()):
        """Write one subagent transcript; `lines` are entries, `raw` extra text lines appended verbatim."""
        self.count += 1
        folder = self.projects / "proj" / session / "subagents"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"agent-{self.count:03d}.jsonl"
        body = "".join(json.dumps(line) + "\n" for line in lines) + "".join(item + "\n" for item in raw)
        path.write_text(body, encoding="utf-8")
        if meta:
            (folder / f"agent-{self.count:03d}.meta.json").write_text(json.dumps(
                {"description": description, "model": model, "effort": effort, "agentType": "general-purpose"}),
                encoding="utf-8")

    def review(self, description, minute, report, *, as_handback=True, session="s1"):
        content = handback(report) if as_handback else text(report)
        self.launch(description, [
            {"type": "user", "timestamp": at(minute), "message": {"role": "user", "content": "review"}},
            assistant(minute + 1, f"r{self.count}", "claude-sonnet-test", content, usage(input=1, output=1)),
        ], model="sonnet", effort="medium", session=session)

    def config(self, client="claude", routes=TABLE):
        path = self.root / f"config-{client}.json"
        document = {"schema_version": 5, "client": client}
        if routes is not None:
            document["routes"] = routes
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def run_cli(self, *extra, config=True, since=SINCE, until=UNTIL):
        argv = (["--config", str(self.config())] if config else [])
        argv += ["route-report", "--since", since, "--projects-dir", str(self.projects)]
        argv += (["--until", until] if until else []) + list(extra)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(argv)
        return code, json.loads(out.getvalue())

    def scenario(self):
        # alfi: one message written on two lines (same id, same usage), a repeated tool id,
        # a request split into an own iteration and an advisor iteration, a malformed line.
        first_usage = usage(input=10, output=5, cache_read=100, write_5m=20, write_1h=30)
        split = usage(iterations=[
            {"type": "message", **usage(input=1, output=2)},
            {"type": "advisor_message", "model": "claude-sonnet-test", **usage(input=50, output=7)},
        ])
        self.launch("build: alfi — fix the parser", [
            {"type": "user", "timestamp": at(0), "message": {"role": "user", "content": "do it"}},
            assistant(1, "m1", "claude-opus-test", [{"type": "tool_use", "id": "t1", "name": "Read", "input": {}}],
                      first_usage),
            assistant(1, "m1", "claude-opus-test", [{"type": "tool_use", "id": "t2", "name": "Edit", "input": {}},
                                                    {"type": "tool_use", "id": "t1", "name": "Read", "input": {}}],
                      first_usage),
            assistant(10, "m2", "claude-opus-test", text("done"), split),
        ], raw=['{"type": "assistant", "timestamp": broken'])
        # bero: a cache write without a lifetime split counts as a 5-minute write.
        self.launch("build: bero — second piece", [
            {"type": "user", "timestamp": at(5), "message": {"role": "user", "content": "do it"}},
            assistant(9, "m3", "claude-haiku-test", [{"type": "tool_use", "id": "t9", "name": "Bash", "input": {}}],
                      usage(input=3, output=4, unsplit=40)),
        ])
        self.review("check: kolo — review alfi", 20, "Summary first.\n**VERDICT:** fix-first\nREVIEWED: alfi, ghost\n")
        self.review("check: lavi — re-review alfi", 40, "VERDICT: fix-first\nREVIEWED: alfi\nFOLLOWS: kolo",
                    as_handback=False)
        self.review("check: mero — re-review alfi", 60, "verdict: **ship**\nreviewed: `alfi`\n*FOLLOWS*: lavi")
        self.review("check: nori — review bero", 25, "Looks good to me, ship it.\nREVIEWED: bero")
        # Unclassed under the table, and launches outside the window.
        self.launch("ovi — explore the repository", [
            {"type": "user", "timestamp": at(2), "message": {"role": "user", "content": "look"}},
            assistant(3, "m4", "claude-haiku-test", text("found"), usage(input=2, output=2)),
        ], model="haiku", effort="medium")
        self.launch("find: pavo — before the window", [
            {"type": "user", "timestamp": at(-90), "message": {"role": "user", "content": "x"}},
            assistant(-89, "m5", "claude-haiku-test", text("x"), usage(input=1000, output=1000)),
        ], model="haiku", effort="medium")
        self.launch("find: rivo — after the window", [
            {"type": "user", "timestamp": at(200), "message": {"role": "user", "content": "x"}},
            assistant(201, "m6", "claude-haiku-test", text("x"), usage(input=1000, output=1000)),
        ], model="haiku", effort="medium")

    def group(self, result, cls):
        rows = [row for row in result["classes"] if row["class"] == cls]
        self.assertEqual(len(rows), 1, rows)
        return rows[0]

    def test_cost_per_class_counts_each_message_once_and_keeps_the_advisor_apart(self):
        self.scenario()
        code, result = self.run_cli("--review-class", "check")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["class_source"], "route_table")
        build = self.group(result, "build")
        self.assertEqual((build["model"], build["effort"], build["launches"]), ("opus", "high", 2))
        self.assertEqual(build["tool_calls"], {"median": 1.5, "total": 3})
        self.assertEqual(build["minutes"], {"median": 7})
        self.assertEqual(build["tokens"], {"input": 14, "output": 11, "cache_read": 100,
                                           "cache_write_5m": 60, "cache_write_1h": 30})
        self.assertEqual(build["advisor"], {"calls": 1, "tokens": {"input": 50, "output": 7, "cache_read": 0,
                                                                   "cache_write_5m": 0, "cache_write_1h": 0}})
        self.assertNotIn("cost", build)
        totals = result["totals"]
        self.assertEqual((totals["launches"], totals["unclassed_launches"], totals["malformed_lines_skipped"]),
                         (7, 1, 1))
        unclassed = self.group(result, None)
        self.assertEqual((unclassed["launches"], unclassed["tokens"]["input"]), (1, 2))
        self.assertEqual([row["class"] for row in result["classes"]], ["build", "check", None])

    def test_reviews_are_attributed_to_the_reviewed_class_and_chained(self):
        self.scenario()
        code, result = self.run_cli("--review-class", "check")
        self.assertEqual(code, 0)
        build = self.group(result, "build")
        self.assertEqual((build["reviewed_launches"], build["share_reviewed"]), (2, 1.0))
        first, follow_up = build["reviews_of_this_work"]["first"], build["reviews_of_this_work"]["follow_up"]
        self.assertEqual({k: v for k, v in first.items() if v}, {"fix-first": 1, "no_verdict_line": 1})
        self.assertEqual({k: v for k, v in follow_up.items() if v}, {"fix-first": 1, "ship": 1})
        self.assertEqual(build["chains"], [{"length": 3, "verdicts": ["fix-first", "fix-first", "ship"],
                                            "reviews": ["kolo", "lavi", "mero"], "reviewed": ["alfi"],
                                            "repeated_rework": True}])
        self.assertEqual(build["repeated_rework"], [["alfi", "kolo", "lavi", "mero"]])
        check = self.group(result, "check")
        self.assertEqual((check["launches"], check["reviewed_launches"], check["chains"]), (4, 0, []))
        totals = result["totals"]
        self.assertEqual(totals["reviews"], 4)
        self.assertEqual(totals["reviews_without_verdict_line"], 1)
        self.assertEqual(totals["unresolved_reviewed_names"], [{"review": "kolo", "name": "ghost"}])
        self.assertEqual(totals["reviews_with_unresolved_names"], 1)
        self.assertEqual((totals["chains"], totals["chains_with_repeated_rework"]), (1, 1))
        self.assertIn("not pieces of work", result["units"]["reviews"])

    def test_a_review_line_alone_marks_a_review_and_an_unknown_value_is_not_guessed(self):
        self.launch("build: alfi — work", [
            {"type": "user", "timestamp": at(0), "message": {"role": "user", "content": "x"}},
            assistant(1, "w1", "claude-opus-test", text("done"), usage(input=1)),
        ])
        self.review("check: kolo — review", 10, "Verdict: looks fine overall\nREVIEWED: alfi")
        self.review("check: lavi — review", 12, "No verdict line here, though I would ship.")
        code, result = self.run_cli()  # no --review-class: only review lines mark a review
        self.assertEqual(code, 0)
        totals = result["totals"]
        self.assertEqual((totals["reviews"], totals["reviews_with_unrecognized_verdict"],
                          totals["reviews_without_verdict_line"]), (1, 1, 0))
        first = self.group(result, "build")["reviews_of_this_work"]["first"]
        self.assertEqual({k: v for k, v in first.items() if v}, {"unrecognized_verdict": 1})

    def test_without_a_table_any_class_shaped_word_is_a_class(self):
        self.scenario()
        self.launch("Explore the code", [
            {"type": "user", "timestamp": at(3), "message": {"role": "user", "content": "x"}},
        ], model="haiku", effort="medium")
        code, result = self.run_cli(config=False)
        self.assertEqual(code, 0)
        self.assertEqual(result["class_source"], "class_name_grammar")
        counts = {row["class"]: row["launches"] for row in result["classes"]}
        self.assertEqual(counts, {"check": 4, "build": 2, "ovi": 1, None: 1})

    def test_prices_add_an_api_equivalent_cost_and_name_unpriced_models(self):
        self.scenario()
        prices = self.root / "prices.json"
        prices.write_text(json.dumps({
            "opus": {"input": 5, "output": 25, "cache_read": 0.5,
                     "cache_write_5m_multiplier": 1.25, "cache_write_1h_multiplier": 2},
            "sonnet": {"input": 3, "output": 15, "cache_read": 0.3,
                       "cache_write_5m_multiplier": 1.25, "cache_write_1h_multiplier": 2},
        }), encoding="utf-8")
        code, result = self.run_cli("--prices", str(prices))
        self.assertEqual(code, 0)
        self.assertIn("not subscription quota", result["cost_basis"])
        cost = self.group(result, "build")["cost"]
        # alfi own: 10*5 + 5*25 + 100*0.5 + 20*5*1.25 + 30*5*2 = 650, plus 1*5 + 2*25 = 55.
        # Advisor (sonnet): 50*3 + 7*15 = 255. bero ran on an unpriced model.
        self.assertAlmostEqual(cost["own_usd"], 705 / 1e6)
        self.assertAlmostEqual(cost["advisor_usd"], 255 / 1e6)
        self.assertEqual(cost["unpriced_models"], ["claude-haiku-test"])

    def test_an_invalid_prices_file_is_invalid_input(self):
        self.scenario()
        prices = self.root / "prices.json"
        prices.write_text(json.dumps({"opus": {"input": 5}}), encoding="utf-8")
        code, result = self.run_cli("--prices", str(prices))
        self.assertEqual((code, result["status"]), (2, "error"))

    def test_a_window_without_launches_fails_distinctly(self):
        self.scenario()
        code, result = self.run_cli(since="2025-01-01T00:00", until="2025-02-01T00:00")
        self.assertEqual((code, result["status"], result["reason"]),
                         (NO_TRANSCRIPTS, "no_transcripts", "no_launch_started_in_window"))
        self.assertNotEqual(NO_TRANSCRIPTS, 2)
        self.projects = self.root / "missing"
        code, result = self.run_cli()
        self.assertEqual((code, result["reason"]), (NO_TRANSCRIPTS, "projects_dir_not_found"))

    def test_the_window_bounds_select_launches_by_their_start(self):
        self.scenario()
        code, result = self.run_cli(since="2026-01-05T08:00", until="2026-01-05T10:03")
        self.assertEqual(code, 0)
        # pavo (-90 min), alfi (0) and ovi (2) start inside; bero (5) and the reviews do not.
        counts = {row["class"]: row["launches"] for row in result["classes"]}
        self.assertEqual(counts, {"build": 1, "find": 1, None: 1})
        self.assertEqual(result["totals"]["reviews"], 0)

    def test_another_client_and_invalid_input_are_refused(self):
        self.scenario()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--client", "codex", "route-report", "--since", SINCE, "--projects-dir", str(self.projects)])
        self.assertEqual(code, 2)
        self.assertIn("Claude Code transcripts only", json.loads(out.getvalue())["error"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--config", str(self.config(client="codex", routes=None)), "route-report",
                         "--since", SINCE, "--projects-dir", str(self.projects)])
        self.assertEqual(code, 2)
        self.assertIn("'codex' is not supported", json.loads(out.getvalue())["error"])
        self.assertEqual(self.run_cli(since="yesterday")[0], 2)
        self.assertEqual(self.run_cli(until="2026-01-05T09:00")[0], 2)
        self.assertEqual(self.run_cli("--review-class", "audit")[0], 2)

    def test_only_the_line_form_of_the_verdict_contract_is_read(self):
        cases = {
            "VERDICT: ship": "ship",
            "  **Verdict:** Fix-First": "fix-first",
            "__VERDICT__: rethink": "rethink",
            "VERDICT: inconclusive  ": "inconclusive",
            "The verdict: ship": "no_verdict_line",
            "I would ship this.": "no_verdict_line",
            "VERDICT: ship.": "unrecognized_verdict",
            "VERDICT: ship\nVERDICT: rethink": "unrecognized_verdict",
        }
        for report, expected in cases.items():
            with self.subTest(report=report):
                self.assertEqual(review_lines(report)["verdict"], expected)
        lines = review_lines("REVIEWED: alfi, `bero`\nreviewed: alfi\nFOLLOWS: kolo")
        self.assertEqual((lines["reviewed"], lines["follows"]), (["alfi", "bero"], "kolo"))


if __name__ == "__main__":
    unittest.main()
