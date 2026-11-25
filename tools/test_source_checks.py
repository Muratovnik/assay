"""Claude source checks: a fetch summary is named once and a contradicted full-read claim continues once; no model runs."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
import unittest.mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import gate, predicates, sources
from runtime.cli import process

SOURCE = "C:\\work\\src\\researcher.py"
PAGE = "https://pmc.ncbi.nlm.nih.gov/articles/PMC12042776/"


def prompt(text="Check the study"):
    return {"type": "user", "message": {"role": "user", "content": text}}


def said(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def tool(name, data, ident):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": ident, "name": name, "input": data}]}}


def returned(ident, text, result=None):
    entry = {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": ident, "content": text}]}}
    return {**entry, "toolUseResult": result} if result is not None else entry


def numbered(first, last):
    return "".join(f"{n}\tline {n}\n" for n in range(first, last + 1))


def read(ident, first, last, total, *, offset=None, limit=None, recorded=True, path=SOURCE):
    """A Read and its result; without a record the range shows only in the numbered text, as in a subagent's."""
    data = {"file_path": path, **({"offset": offset} if offset else {}), **({"limit": limit} if limit else {})}
    result = ({"type": "text", "file": {"filePath": path, "content": "...", "startLine": first,
                                        "numLines": last - first + 1, "totalLines": total}} if recorded else None)
    return [tool("Read", data, ident), returned(ident, numbered(first, last), result)]


class SourceCheckTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.now = 1000.0
        self.base = {"session_id": "session", "cwd": "work"}

    def fetch(self, **extra):
        event = {**self.base, "hook_event_name": "PostToolUse", "tool_name": "WebFetch", "prompt_id": "p1",
                 "tool_input": {"url": PAGE, "prompt": "Quote the results"}, **extra}
        return sources.fetched(event, self.directory, clock=lambda: self.now)

    def search(self, **extra):
        event = {**self.base, "hook_event_name": "PostToolUse", "tool_name": "WebSearch", "prompt_id": "p1",
                 "tool_input": {"query": "vendor client retries"}, **extra}
        return sources.searched(event, self.directory, clock=lambda: self.now)

    def transcript(self, *entries, name="session.jsonl"):
        path = self.directory / name
        flat = [item for entry in entries for item in (entry if isinstance(entry, list) else [entry])]
        path.write_text("".join(json.dumps(entry) + "\n" for entry in flat), encoding="utf-8")
        return str(path)

    def stop(self, *entries, last="", **extra):
        return sources.stopped({**self.base, "hook_event_name": "Stop", "transcript_path": self.transcript(*entries),
                                "last_assistant_message": last, **extra})

    def feedback(self, result, event="Stop"):
        self.assertNotIn("decision", result)
        self.assertIn("hookSpecificOutput", result, "the check said nothing")
        output = result["hookSpecificOutput"]
        self.assertEqual({"hookEventName", "additionalContext"}, set(output))
        self.assertEqual(event, output["hookEventName"])
        return output["additionalContext"]

    def test_the_first_fetch_of_a_request_gets_the_note_and_later_fetches_do_not(self):
        text = self.feedback(self.fetch(), "PostToolUse")
        self.assertIn("not the page's text", text)
        # Some documentation sites return the page itself, which no download improves on.
        self.assertIn("a WebFetch result is usually a model's answer", text)
        self.assertIn("Some documentation sites return the page itself; such a result is the page's text and needs "
                      "no download.", text)
        # The label is unconditional; the download is asked for only on its stated condition.
        self.assertIn("A conclusion that rests on the fetch summary is stated as resting on it.", text)
        self.assertIn("shell download", text)
        self.assertIn("when that conclusion depends on exact wording, a number, a table or code", text)
        self.assertIn("a narrow fact the summary quotes from an authoritative page needs only the label", text)
        # The hook cannot know which tools the session has, so it names none.
        for name in ("curl", "gh ", "wget"):
            self.assertNotIn(name, text)
        self.assertEqual({}, self.fetch())
        self.assertEqual({}, self.fetch(tool_use_id="another"))

    def test_a_new_request_or_another_agent_gets_the_note_again(self):
        self.fetch()
        self.assertTrue(self.fetch(prompt_id="p2"))
        self.assertTrue(self.fetch(agent_id="worker"))
        self.assertEqual({}, self.fetch(agent_id="worker"))

    def test_a_fetch_without_a_prompt_id_is_noted_once_per_agent(self):
        self.assertTrue(self.fetch(prompt_id=None))
        self.assertEqual({}, self.fetch(prompt_id=None))

    def test_the_web_fetch_agent_gets_no_fetch_note(self):
        # Its WebFetch result is the page's text, and it has no shell to download the page.
        self.assertEqual({}, self.fetch(agent_id="f1", agent_type="web-fetch"))
        # Its result kept no key: another agent's first fetch in the same request is still noted.
        self.assertTrue(self.fetch(agent_id="f1", agent_type="general-purpose"))

    def test_other_tools_or_missing_state_get_no_note(self):
        self.assertEqual({}, self.fetch(tool_name="WebSearch"))
        event = {**self.base, "hook_event_name": "PostToolUse", "tool_name": "WebFetch", "prompt_id": "p1"}
        self.assertEqual({}, sources.fetched(event, None))
        self.assertEqual({}, self.fetch(session_id=""))

    def test_the_first_search_of_a_request_gets_the_note_and_later_searches_do_not(self):
        text = self.feedback(self.search(), "PostToolUse")
        self.assertIn("search results are found, not read", text)
        # What meets the client's request to include its sources, and which unopened result stays named.
        self.assertIn("the ones the conclusion rests on, each labelled with how it was read", text)
        self.assertIn("at most one line with their count and kind", text)
        self.assertIn("named only if it could change the conclusion, with why", text)
        self.assertEqual({}, self.search())
        self.assertEqual({}, self.search(tool_use_id="another"))

    def test_a_new_request_or_another_agent_gets_the_search_note_again(self):
        self.search()
        self.assertTrue(self.search(prompt_id="p2"))
        self.assertTrue(self.search(agent_id="worker"))
        self.assertEqual({}, self.search(agent_id="worker"))

    def test_a_search_and_a_fetch_in_one_request_each_get_their_own_note(self):
        self.assertIn("not the page's text", self.feedback(self.fetch(), "PostToolUse"))
        self.assertIn("found, not read", self.feedback(self.search(), "PostToolUse"))
        self.assertEqual({}, self.fetch())
        self.assertEqual({}, self.search())

    def test_another_tool_or_missing_state_gets_no_search_note(self):
        self.assertEqual({}, self.search(tool_name="WebFetch"))
        event = {**self.base, "hook_event_name": "PostToolUse", "tool_name": "WebSearch", "prompt_id": "p1"}
        self.assertEqual({}, sources.searched(event, None))
        self.assertEqual({}, self.search(session_id=""))

    def test_a_claim_about_a_partly_read_file_continues_the_turn(self):
        text = self.feedback(self.stop(prompt(), read("r1", 1, 200, 900, limit=200),
                                       said("Я прочитал researcher.py целиком: фильтр по умолчанию keyword.")))
        self.assertIn("researcher.py: only lines 1-200 of 900 were read", text)
        self.assertIn("The answer already given stands", text)

    def test_a_default_read_cut_short_by_the_tool_counts_as_partial(self):
        text = self.feedback(self.stop(prompt(), read("r1", 1, 2000, 2400), said("I read researcher.py in full.")))
        self.assertIn("lines 1-2000 of 2400", text)

    def test_a_full_read_or_chunks_that_reach_the_end_stay_silent(self):
        claim = said("I read researcher.py in full.")
        self.assertEqual({}, self.stop(prompt(), read("r1", 1, 900, 900), claim))
        self.assertEqual({}, self.stop(prompt(), read("r1", 1, 500, 900, limit=500),
                                       read("r2", 501, 900, 900, offset=501, limit=500), claim))
        # A full read in an earlier turn of the session still counts.
        self.assertEqual({}, self.stop(prompt("first"), read("r0", 1, 900, 900), said("ok"), prompt(),
                                       read("r1", 10, 20, 900, offset=10, limit=11), claim))

    def test_a_gap_between_chunks_is_partial(self):
        text = self.feedback(self.stop(prompt(), read("r1", 1, 300, 900, limit=300),
                                       read("r2", 601, 900, 900, offset=601, limit=300),
                                       said("researcher.py прочитан полностью.")))
        self.assertIn("lines 1-300, 601-900 of 900", text)

    def test_a_subagent_transcript_without_ranges_uses_the_numbered_lines(self):
        partial = [read("r1", 1, 100, 0, limit=100, recorded=False)]
        report = said("Read researcher.py end to end.")
        path = self.transcript(prompt(), *partial, report, name="agent.jsonl")
        event = {**self.base, "hook_event_name": "SubagentStop", "agent_id": "worker",
                 "agent_transcript_path": path, "last_assistant_message": ""}
        self.assertIn("only lines 1-100 were read", self.feedback(sources.stopped(event), "SubagentStop"))
        # A last chunk shorter than its limit reached the end of the file.
        whole = [read("r1", 1, 100, 0, limit=100, recorded=False),
                 read("r2", 101, 140, 0, offset=101, limit=100, recorded=False)]
        event["agent_transcript_path"] = self.transcript(prompt(), *whole, report, name="agent2.jsonl")
        self.assertEqual({}, sources.stopped(event))
        # A plain Read without a recorded range is not evidence of a partial read.
        plain = [read("r1", 1, 100, 0, recorded=False)]
        event["agent_transcript_path"] = self.transcript(prompt(), *plain, report, name="agent3.jsonl")
        self.assertEqual({}, sources.stopped(event))

    def test_a_claim_is_compared_with_the_file_its_own_clause_names(self):
        partial = read("r1", 1, 200, 900, limit=200)
        # The claim word speaks of something else on the line; the partly read file sits in another clause.
        for line in ("Если закоммитить правки в `researcher.py`, в коммит целиком попадут и чужие файлы.",
                     "Из researcher.py прочитаны строки 1–200. AGENTS.md прочитан целиком.",
                     "The prefix is handled in full (`_route` in `src/researcher.py`).",
                     "docs/guide.md read in full; researcher.py lines 1-200 set the default.",
                     'researcher.py still says "read in full" in its header.'):
            with self.subTest(line=line):
                self.assertEqual({}, self.stop(prompt(), partial, said(line)))
        # The clause that names the file still holds it to the claim: a list after the claim, a claim in a parenthesis.
        for line in ("Read in full: notes.md, researcher.py and the guide.", "`researcher.py` (read in full) sets it."):
            with self.subTest(line=line):
                self.assertIn("researcher.py: only lines 1-200 of 900", self.feedback(self.stop(prompt(), partial, said(line))))

    def test_a_claim_names_the_file_it_spells_out_not_another_of_a_similar_name(self):
        other = "C:\\work\\old\\researcher.py"
        whole, cut = read("r1", 1, 900, 900), read("r2", 1, 200, 900, limit=200, path=other)
        # A path tells which of two files of one name was meant.
        self.assertEqual({}, self.stop(prompt(), whole, cut, said("I read src/researcher.py in full.")))
        text = self.feedback(self.stop(prompt(), whole, cut, said("I read old/researcher.py in full.")))
        self.assertIn("researcher.py: only lines 1-200 of 900", text)
        # A bare name holds when one file of that name was read in full.
        self.assertEqual({}, self.stop(prompt(), whole, cut, said("I read researcher.py in full.")))
        # A longer name that ends with a read file's name is another file.
        common = read("r3", 1, 20, 300, limit=20, path="C:\\work\\common.md")
        self.assertEqual({}, self.stop(prompt(), common, said("batch-common.md read in full.")))
        self.assertIn("common.md: only lines 1-20 of 300",
                      self.feedback(self.stop(prompt(), common, said("common.md read in full."))))

    def test_a_claim_about_a_stated_range_counts_the_reads_of_that_range(self):
        chunks = [read("r1", 1, 200, 900, limit=200), read("r2", 201, 400, 900, offset=201, limit=200)]
        for line in ("researcher.py lines 1–400 read in full.", "Read researcher.py:120-380 in full.",
                     "[researcher.py#L10-L20](researcher.py#L10-L20) прочитан целиком."):
            with self.subTest(line=line):
                self.assertEqual({}, self.stop(prompt(), *chunks, said(line)))
        # A range beyond what was read, and a claim without one, still hold.
        for line in ("researcher.py lines 1-600 read in full.", "researcher.py read in full (1–900).",
                     "researcher.py read in full."):
            with self.subTest(line=line):
                self.assertIn("researcher.py: only lines 1-200, 201-400 of 900",
                              self.feedback(self.stop(prompt(), *chunks, said(line))))

    def test_common_report_forms_tie_the_claim_to_every_file_they_list(self):
        files = {"parser": "C:\\work\\src\\parser.py", "reports": "C:\\work\\src\\reports.py",
                 "hooks": "C:\\work\\docs\\how-to\\hooks.md", "skill": "C:\\work\\skills\\pace-log\\SKILL.md",
                 "classify": "C:\\work\\classify.py", "agents": "C:\\work\\inputs\\instructions\\AGENTS.md"}
        partial = [read(f"p{n}", 1, 200, 900, limit=200, path=path) for n, path in enumerate(files.values())]
        whole = [read(f"w{n}", 1, 900, 900, path=path) for n, path in enumerate(files.values())]
        forms = {
            "| `parser.py` | read in full |": ["parser.py"],
            "| parser.py | целиком | 900 строк |": ["parser.py"],
            "| `inputs/instructions/AGENTS.md` | Read in full |": ["AGENTS.md"],
            "Read parser.py, reports.py and hooks.md in full.": ["parser.py", "reports.py", "hooks.md"],
            "Я прочитал parser.py, reports.py и hooks.md целиком.": ["parser.py", "reports.py", "hooks.md"],
            "полностью прочитаны README, `skills/pace-log/SKILL.md`, `classify.py`": ["SKILL.md", "classify.py"],
            "parser.py, read in full, sets the default.": ["parser.py"],
            "Read parser.py in full, reports.py too.": ["parser.py", "reports.py"],
            "parser.py — прочитан целиком, reports.py — тоже": ["parser.py", "reports.py"],
            "Read the parser in full (`src/parser.py`).": ["parser.py"],
            "Прочитал целиком справку по хукам (docs/how-to/hooks.md).": ["hooks.md"],
            "[the parser](C:/work/src/parser.py) read in full.": ["parser.py"],
            "Read parser.py in full (approx. 900 lines).": ["parser.py"],
            # A name the transcript shows no Read of is still a list item and does not end the list.
            "полностью прочитаны parser.py, notes.txt, reports.py": ["parser.py", "reports.py"],
            "Прочитал целиком parser.py, README и reports.py.": ["parser.py", "reports.py"],
            "Read parser.py, notes.txt, reports.py in full.": ["parser.py", "reports.py"],
            "Read in full (notes.txt, `src/parser.py`).": ["parser.py"],
        }
        for line, names in forms.items():
            with self.subTest(line=line):
                text = self.feedback(self.stop(prompt(), *partial, said(line)))
                for name in names:
                    self.assertIn(f"{name}: only lines 1-200 of 900", text)
                self.assertEqual({}, self.stop(prompt(), *whole, said(line)))

    def test_words_after_a_name_without_a_read_still_end_the_list(self):
        partial = [read("p1", 1, 200, 900, limit=200, path="C:\\work\\src\\parser.py"),
                   read("p2", 1, 200, 900, limit=200, path="C:\\work\\src\\reports.py")]
        for line in ("Read parser.py in full, notes.txt was skipped, reports.py too.",
                     "Read parser.py in full, notes.txt, then skimmed reports.py."):
            with self.subTest(line=line):
                text = self.feedback(self.stop(prompt(), *partial, said(line)))
                self.assertIn("parser.py: only lines 1-200 of 900", text)
                self.assertNotIn("reports.py", text)

    def test_a_range_counts_only_when_it_is_attached_to_the_name(self):
        cut = read("r1", 1, 200, 900, limit=200, path="C:\\work\\src\\parser.py")
        for line in ("Read parser.py in full and found the bug at line 120.", "Read parser.py in full (see line 40).",
                     "Read parser.py in full - the tokenizer is at lines 10-20."):
            with self.subTest(line=line):
                self.assertIn("parser.py: only lines 1-200 of 900", self.feedback(self.stop(prompt(), cut, said(line))))
        longer = read("r2", 1, 400, 900, limit=400, path="C:\\work\\src\\parser.py")
        for line in ("Read parser.py:120-380 in full.", "[parser.py#L10-L20](parser.py#L10-L20) read in full.",
                     "parser.py lines 1–400 read in full.", "parser.py (1–400) read in full."):
            with self.subTest(line=line):
                self.assertEqual({}, self.stop(prompt(), longer, said(line)))
        # The same reads leave a claim about the whole file contradicted.
        self.assertIn("parser.py: only lines 1-400 of 900",
                      self.feedback(self.stop(prompt(), longer, said("parser.py read in full."))))

    def test_a_file_never_read_with_the_read_tool_stays_silent(self):
        shell = tool("Bash", {"command": f"cat {SOURCE}"}, "b1")
        self.assertEqual({}, self.stop(prompt(), shell, returned("b1", "..."), said("I read researcher.py in full.")))

    def test_a_page_opened_only_through_webfetch_continues_the_turn(self):
        fetch = [tool("WebFetch", {"url": PAGE, "prompt": "Quote"}, "w1"), returned("w1", "A summary of the page")]
        text = self.feedback(self.stop(prompt(), fetch, said("I read PMC12042776 in full; Claude was not significant.")))
        self.assertIn(PAGE + ": opened only through WebFetch", text)
        # A site that returns the page itself makes the claim true, so the objection leaves that open.
        self.assertIn("whose result is a model's summary unless the site returned the page itself", text)
        downloaded = [tool("Bash", {"command": f"curl -sL -A Mozilla {PAGE} -o page.html"}, "b1"), returned("b1", "")]
        self.assertEqual({}, self.stop(prompt(), fetch, downloaded, said("I read PMC12042776 in full.")))

    def test_without_a_claim_or_after_a_continuation_the_check_is_silent(self):
        partial = read("r1", 1, 200, 900, limit=200)
        self.assertEqual({}, self.stop(prompt(), partial, said("researcher.py lines 1-200 set the default.")))
        self.assertEqual({}, self.stop(prompt(), partial, said("I read researcher.py in full."), stop_hook_active=True))

    def test_a_claim_from_an_earlier_turn_or_a_read_before_compaction_is_not_counted(self):
        partial = read("r1", 1, 200, 900, limit=200)
        self.assertEqual({}, self.stop(prompt("first"), partial, said("I read researcher.py in full."),
                                       prompt(), said("Done.")))
        boundary = {"type": "system", "subtype": "compact_boundary"}
        self.assertEqual({}, self.stop(partial, boundary, prompt(), said("I read researcher.py in full.")))

    def test_the_final_message_is_checked_even_before_the_transcript_holds_it(self):
        text = self.feedback(self.stop(prompt(), read("r1", 1, 200, 900, limit=200),
                                       last="I read researcher.py in full."))
        self.assertIn("researcher.py", text)

    def test_a_turn_without_a_claim_stops_reading_at_its_start(self):
        consumed = []
        original = sources._lines

        def counted(path):
            for line in original(path):
                consumed.append(line)
                yield line

        earlier = [prompt("first"), *read("r0", 1, 200, 900, limit=200), said("ok")]
        with unittest.mock.patch.object(sources, "_lines", counted):
            self.assertEqual({}, self.stop(*earlier, prompt(), said("Done.")))
            self.assertEqual(2, len([line for line in consumed if line.strip()]))  # the reply and its prompt
            consumed.clear()
            # A claim in the final message alone still reaches the earlier read.
            text = self.feedback(self.stop(*earlier, prompt(), said("Done."), last="I read researcher.py in full."))
        self.assertIn("only lines 1-200 of 900", text)
        self.assertGreater(len([line for line in consumed if line.strip()]), 2)

    def test_an_unreadable_transcript_stays_silent(self):
        event = {**self.base, "hook_event_name": "Stop", "transcript_path": str(self.directory / "missing.jsonl"),
                 "last_assistant_message": "I read researcher.py in full."}
        self.assertEqual({}, sources.stopped(event))


class SourceCheckRuntimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.environment = {"CLAUDE_PLUGIN_DATA": str(self.directory / "data")}
        self.fetch = {"session_id": "session", "cwd": "work", "hook_event_name": "PostToolUse", "prompt_id": "p1",
                      "tool_name": "WebFetch", "tool_use_id": "w1", "tool_input": {"url": PAGE, "prompt": "Quote"}}
        self.search = {"session_id": "session", "cwd": "work", "hook_event_name": "PostToolUse", "prompt_id": "p1",
                       "tool_name": "WebSearch", "tool_use_id": "s1", "tool_input": {"query": "vendor client retries"}}

    def configured(self, **options):
        path = self.directory / "hooks.json"
        path.write_text(json.dumps({**options, "state_dir": str(self.directory / "data")}), encoding="utf-8")
        return {"ASSAY_HOOK_CONFIG": str(path)}

    def test_the_runtime_returns_the_fetch_note_for_claude_only(self):
        result, error = process(self.fetch, "claude", self.environment)
        self.assertIsNone(error)
        self.assertIn("not the page's text", result["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(({}, None), process({**self.fetch, "prompt_id": "p2"}, "codex", self.environment))

    def test_the_runtime_returns_the_search_note_for_claude_only(self):
        result, error = process(self.search, "claude", self.environment)
        self.assertIsNone(error)
        self.assertIn("found, not read", result["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(({}, None), process({**self.search, "prompt_id": "p2"}, "codex", self.environment))

    def test_the_search_note_and_the_fetch_note_turn_off_separately(self):
        environment = self.configured(disabled_rules=["search-note"])
        self.assertEqual(({}, None), process({**self.search, "prompt_id": "p7"}, "claude", environment))
        self.assertIn("not the page's text",
                      process({**self.fetch, "prompt_id": "p7"}, "claude", environment)[0]["hookSpecificOutput"]["additionalContext"])
        environment = self.configured(disabled_rules=["fetch-note"])
        self.assertEqual(({}, None), process({**self.fetch, "prompt_id": "p8"}, "claude", environment))
        self.assertIn("found, not read",
                      process({**self.search, "prompt_id": "p8"}, "claude", environment)[0]["hookSpecificOutput"]["additionalContext"])

    def test_each_source_check_rule_turns_off_only_its_own_note(self):
        environment = self.configured(disabled_rules=["read-claims"])
        self.assertIn("additionalContext", process(self.fetch, "claude", environment)[0]["hookSpecificOutput"])
        environment = self.configured(disabled_rules=["fetch-note"])
        self.assertEqual(({}, None), process({**self.fetch, "prompt_id": "p9"}, "claude", environment))
        path = self.directory / "session.jsonl"
        entries = [prompt(), *read("r1", 1, 200, 900, limit=200), said("I read researcher.py in full.")]
        path.write_text("".join(json.dumps(entry) + "\n" for entry in entries), encoding="utf-8")
        stop = {"session_id": "session", "cwd": "work", "hook_event_name": "Stop", "transcript_path": str(path),
                "last_assistant_message": "I read researcher.py in full."}
        self.assertIn("only lines 1-200", process(stop, "claude", environment)[0]["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(({}, None), process(stop, "claude", self.configured(disabled_rules=["read-claims"])))
        result, _ = process(stop, "claude", self.environment)
        self.assertIn("only lines 1-200 of 900", result["hookSpecificOutput"]["additionalContext"])

    def test_the_skill_gate_keeps_priority_on_stop(self):
        path = self.directory / "session.jsonl"
        entries = [prompt(), *read("r1", 1, 200, 900, limit=200),
                   said("Using `assay:evidence-research` to check.\n\nI read researcher.py in full.")]
        path.write_text("".join(json.dumps(entry) + "\n" for entry in entries), encoding="utf-8")
        stop = {"session_id": "session", "cwd": "work", "hook_event_name": "Stop", "transcript_path": str(path),
                "last_assistant_message": "I read researcher.py in full."}
        result, _ = process(stop, "claude", self.environment)
        self.assertIn("Assay skill gate", result["hookSpecificOutput"]["additionalContext"])

    def test_only_the_claude_manifest_routes_fetch_and_search_results_to_the_hook(self):
        claude = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
        codex = json.loads((ROOT / "hooks/codex.json").read_text(encoding="utf-8"))["hooks"]
        self.assertEqual("^(Agent|Task|WebFetch|WebSearch)$", claude["PostToolUse"][0]["matcher"])
        self.assertNotIn("PostToolUse", codex)


DOCS = "https://docs.example.dev/en/hooks"
# The line Claude Code ends a WebFetch result with when the answer covers part of a long page, as it appears
# in recorded results; the result object keeps the fields a transcript's toolUseResult shows.
CUT_LINE = ("[WebFetch note: this page's text is 286092 characters long and the answer above covers only characters "
            "0 to 100000; the final 186092 were not read — to read on, call WebFetch again with the same url and "
            "offset: 100000.]")


def fetched_result(text, url=DOCS):
    return {"bytes": 286102, "code": 200, "codeText": "OK", "result": text, "durationMs": 900, "url": url}


class CutPageTests(unittest.TestCase):
    """A WebFetch result that covers only part of a page is named once per page, with the page's Markdown address."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.environment = {"CLAUDE_PLUGIN_DATA": str(self.directory / "data")}

    def event(self, url=DOCS, text="The hooks are listed below.\n\n" + CUT_LINE, *, response=None, data=None, **extra):
        return {"session_id": "session", "cwd": "work", "hook_event_name": "PostToolUse", "prompt_id": "p1",
                "tool_name": "WebFetch", "tool_input": data or {"url": url, "prompt": "List the hook events"},
                "tool_response": fetched_result(text, url) if response is None else response, **extra}

    def note(self, event):
        result = sources.cut(event, self.directory)
        return result["hookSpecificOutput"]["additionalContext"] if result else None

    def test_a_cut_page_is_named_with_its_size_the_part_read_and_its_markdown_address(self):
        text = self.note(self.event())
        self.assertIn("its text is 286092 characters, and this answer covers characters 0 to 100000", text)
        self.assertIn("`https://docs.example.dev/en/hooks.md`", text)
        self.assertIn("download its text once with a shell command and search the file", text)
        self.assertIn("Check that the download is Markdown, not an HTML or error page", text)

    def test_the_markdown_address_drops_query_fragment_and_trailing_slash(self):
        cases = {"https://docs.example.dev/en/hooks/": ("https://docs.example.dev/en/hooks.md", True),
                 "https://docs.example.dev/en/hooks?tab=1#events": ("https://docs.example.dev/en/hooks.md", True),
                 "https://docs.example.dev/en/hooks.md": ("https://docs.example.dev/en/hooks.md", False),
                 "http://docs.example.dev/guide.MD": ("http://docs.example.dev/guide.MD", False)}
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(expected, sources.markdown_address(url))
        for url in ("https://docs.example.dev/", "https://docs.example.dev", "ftp://docs.example.dev/a", "not a url",
                    None, "https://[::1/a"):
            with self.subTest(url=url):
                self.assertIsNone(sources.markdown_address(url))

    def test_an_address_that_is_already_markdown_or_names_no_page_gets_the_fitting_sentence(self):
        self.assertIn("This address already names the page's Markdown: `https://docs.example.dev/en/hooks.md`",
                      self.note(self.event("https://docs.example.dev/en/hooks.md")))
        text = self.note(self.event("https://docs.example.dev/"))
        self.assertIn("Download the page itself.", text)
        self.assertNotIn(".md", text)

    def test_one_note_per_page_request_and_agent_and_reading_on_is_the_same_page(self):
        self.assertTrue(self.note(self.event()))
        self.assertIsNone(self.note(self.event()))
        on = self.event(data={"url": DOCS, "prompt": "Continue", "offset": 100000},
                        text="More hooks.\n\n" + CUT_LINE.replace("0 to 100000", "100000 to 200000"))
        self.assertIsNone(self.note(on))
        self.assertIsNone(self.note(self.event(DOCS + "/#events")))
        self.assertTrue(self.note(self.event("https://docs.example.dev/en/settings")))
        self.assertTrue(self.note(self.event(prompt_id="p2")))
        self.assertTrue(self.note(self.event(agent_id="worker")))

    def test_a_whole_page_another_tool_the_web_fetch_agent_or_missing_state_get_no_note(self):
        self.assertIsNone(self.note(self.event(text="The hooks are listed below.")))
        # The client's line must close the result, not appear inside a quoted page.
        self.assertIsNone(self.note(self.event(text=CUT_LINE + "x" * 5000)))
        self.assertIsNone(self.note({**self.event(), "tool_name": "WebSearch"}))
        self.assertIsNone(self.note(self.event(agent_id="f1", agent_type="web-fetch")))
        self.assertIsNone(self.note(self.event(response="not an object")))
        self.assertIsNone(self.note(self.event(response={"result": None})))
        self.assertEqual({}, sources.cut(self.event(), None))
        self.assertIsNone(self.note(self.event(session_id="")))
        # A plain string response, as a failed or older call may carry, is read the same way.
        self.assertTrue(self.note(self.event(response="Answer.\n\n" + CUT_LINE, prompt_id="p9")))

    def test_the_runtime_joins_the_fetch_note_and_the_cut_note_and_each_turns_off_alone(self):
        result, error = process(self.event(), "claude", self.environment)
        self.assertIsNone(error)
        text = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("not the page's text", text)
        self.assertIn("covers characters 0 to 100000", text)
        self.assertLess(text.index("not the page's text"), text.index("covers characters"))
        # Reading on in the same request brings neither again.
        self.assertEqual(({}, None), process(self.event(tool_use_id="w2"), "claude", self.environment))
        path = self.directory / "hooks.json"
        for rule, kept, gone in (("truncation-note", "not the page's text", "covers characters"),
                                 ("fetch-note", "covers characters", "not the page's text")):
            with self.subTest(rule=rule):
                path.write_text(json.dumps({"disabled_rules": [rule], "state_dir": str(self.directory / rule)}),
                                encoding="utf-8")
                text = process(self.event(), "claude", {"ASSAY_HOOK_CONFIG": str(path)})[0][
                    "hookSpecificOutput"]["additionalContext"]
                self.assertIn(kept, text)
                self.assertNotIn(gone, text)
        self.assertEqual(({}, None), process(self.event(prompt_id="p3"), "codex", self.environment))


QUESTION = {"questions": [{"question": "Which approach?", "header": "Approach", "multiSelect": False,
                           "options": [{"label": "A", "description": "1.2x faster"},
                                       {"label": "B", "description": "no change"}]}]}
PLANNING_REQUEST = {"id": "X-1", "kind": "decision", "prompt": "Ship it?", "fields": [{"type": "choice"}]}
PLANNING_BATCH = {"id": "X-1", "comment": {"body": "done"},
                 "questions": [{"kind": "question", "prompt": "Which?", "fields": [{"type": "text"}]}]}


class OwnerQuestionTests(unittest.TestCase):
    """The first question to the owner of a request is refused once with the note on its sources; the retry passes."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.environment = {"CLAUDE_PLUGIN_DATA": str(self.directory / "data")}

    def pre(self, tool="AskUserQuestion", data=None, **extra):
        return {"session_id": "session", "cwd": "work", "hook_event_name": "PreToolUse", "prompt_id": "p1",
                "tool_name": tool, "tool_input": QUESTION if data is None else data, **extra}

    def configured(self, **options):
        path = self.directory / "hooks.json"
        path.write_text(json.dumps({**options, "state_dir": str(self.directory / "data")}), encoding="utf-8")
        return {"ASSAY_HOOK_CONFIG": str(path)}

    def refusal(self, event, environment=None):
        result, error = process(event, "claude", self.environment if environment is None else environment)
        self.assertIsNone(error)
        output = result.get("hookSpecificOutput", {})
        if not output:
            return None
        self.assertEqual("deny", output["permissionDecision"])
        self.assertNotIn("additionalContext", output)
        return output["permissionDecisionReason"]

    def loaded(self, skill="assay:critical-discussion", **extra):
        process(self.pre("Skill", {"skill": skill}, **extra), "claude", self.environment)

    def test_which_calls_put_a_question_to_the_owner(self):
        for tool, data in (("AskUserQuestion", QUESTION), ("AskUserQuestion", {}),
                           ("mcp__planning__create_work_item_request", PLANNING_REQUEST),
                           ("mcp__plugin_tracker_planning__create_work_item_request", {}),
                           ("mcp__planning__apply_work_item_changes", PLANNING_BATCH)):
            with self.subTest(tool=tool):
                self.assertTrue(predicates.owner_question(tool, data))
        for tool, data in (("mcp__planning__apply_work_item_changes", {"id": "X-1", "comment": {"body": "x"}}),
                           ("mcp__planning__apply_work_item_changes", {"questions": []}),
                           ("mcp__planning__apply_work_item_changes", {"questions": "Which?"}),
                           ("mcp__planning__apply_work_item_changes", "not an object"),
                           ("mcp__planning__get_work_item_request", {}), ("create_work_item_request", {}),
                           ("mcp__planning__create_work_item_request_list", {}), ("Bash", {"command": "x"}), (None, {})):
            with self.subTest(tool=tool, data=data):
                self.assertFalse(predicates.owner_question(tool, data))

    def test_the_first_question_of_a_request_is_refused_with_the_note_and_the_retry_passes(self):
        self.loaded()
        reason = self.refusal(self.pre())
        self.assertTrue(reason.startswith("Assay: Assay source check: "))
        # What the item asks for: a command or read made for this question and its revision, else an assumption.
        self.assertIn("each rests on a command or read made for this question, named with the revision", reason)
        self.assertIn("or is marked as an assumption", reason)
        self.assertIn("A figure carried over from a report, a summary, memory or an earlier message is not a source",
                      reason)
        self.assertIn("This call was not run; the same call, or the corrected one, passes when repeated.", reason)
        # The note never repeats the question it holds.
        self.assertNotIn("Which approach?", reason)
        self.assertNotIn("1.2x", reason)
        self.assertIsNone(self.refusal(self.pre()))
        # A corrected question and a later question of the same request pass too.
        self.assertIsNone(self.refusal(self.pre(data={"questions": [{"question": "Other?", "options": []}]})))

    def test_a_new_request_or_another_agent_is_refused_once_again(self):
        self.loaded()
        self.loaded(prompt_id="p2")
        self.loaded(agent_id="worker")
        self.assertTrue(self.refusal(self.pre()))
        self.assertTrue(self.refusal(self.pre(prompt_id="p2")))
        self.assertIsNone(self.refusal(self.pre(prompt_id="p2")))
        self.assertTrue(self.refusal(self.pre(agent_id="worker")))
        self.assertIsNone(self.refusal(self.pre(agent_id="worker")))

    def test_a_planning_question_is_refused_on_the_first_call_and_passes_on_the_second(self):
        for tool, data in (("mcp__planning__create_work_item_request", PLANNING_REQUEST),
                           ("mcp__planning__apply_work_item_changes", PLANNING_BATCH)):
            with self.subTest(tool=tool):
                event = self.pre(tool, data, prompt_id=tool)
                self.assertIn("Assay source check", self.refusal(event))
                self.assertIsNone(self.refusal(event))

    def test_a_batch_write_without_questions_passes_and_leaves_the_next_question_refused(self):
        batch = self.pre("mcp__planning__apply_work_item_changes", {"id": "X-1", "checklist_ticks": [{"item_id": "a"}]})
        self.assertIsNone(self.refusal(batch))
        self.assertIn("Assay source check",
                      self.refusal(self.pre("mcp__planning__create_work_item_request", PLANNING_REQUEST)))

    def test_the_skill_note_on_the_same_question_joins_the_one_refusal(self):
        # critical-discussion is not loaded, so its row refuses this question too; one refusal carries both.
        reason = self.refusal(self.pre())
        self.assertIn("assay:critical-discussion", reason)
        self.assertIn("Assay source check", reason)
        self.assertLess(reason.index("assay:critical-discussion"), reason.index("Assay source check"))
        self.assertIsNone(self.refusal(self.pre()))

    def test_the_rule_turns_off_alone_and_codex_or_missing_state_get_nothing(self):
        environment = self.configured(disabled_rules=["question-sources"])
        self.assertIsNone(self.refusal(self.pre("mcp__planning__create_work_item_request", PLANNING_REQUEST),
                                       environment))
        # The skill note keeps refusing without it, alone.
        reason = self.refusal(self.pre(), environment)
        self.assertIn("assay:critical-discussion", reason)
        self.assertNotIn("Assay source check", reason)
        self.assertIsNone(self.refusal(self.pre(), environment))
        self.assertEqual(({}, None), process(self.pre(prompt_id="p6"), "codex", self.environment))
        self.assertEqual({}, sources.asked(self.pre(), None))
        self.assertEqual({}, sources.asked(self.pre(session_id=""), self.directory))
        self.assertEqual({}, sources.asked({**self.pre(), "hook_event_name": "PostToolUse"}, self.directory))

    def test_the_hook_entry_sends_every_owner_question_the_full_path(self):
        for tool, data in (("AskUserQuestion", QUESTION), ("mcp__planning__create_work_item_request", PLANNING_REQUEST),
                           ("mcp__planning__apply_work_item_changes", PLANNING_BATCH)):
            with self.subTest(tool=tool):
                self.assertFalse(gate.quiet(json.dumps(self.pre(tool, data)).encode()))
        quiet = self.pre("mcp__planning__apply_work_item_changes", {"id": "X-1", "comment": {"body": "x"}})
        self.assertTrue(gate.quiet(json.dumps(quiet).encode()))
        # Claude Code runs the hook for these tools: the catch-all PreToolUse matcher covers MCP names.
        import re
        claude = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
        for tool in ("AskUserQuestion", "mcp__planning__create_work_item_request"):
            self.assertTrue(any(re.search(group["matcher"], tool) for group in claude), tool)


if __name__ == "__main__":
    unittest.main()
