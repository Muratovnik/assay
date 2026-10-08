"""Narrow deterministic checks for the comparison fixtures, not a model runner.

Run: python -B comparison_checks.py --case B1-M --work /path/to/artifact
Exit 0: criteria met without unresolved contradictory execution evidence.
Exit 1: a criterion refuted; 2: missing or unresolved contradictory evidence.
Subject code/tests execute only in disposable copies. This is not an OS sandbox.
Evaluator executions never establish which checks the subject previously ran.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import csv
import hashlib
from html.parser import HTMLParser
import io
import json
import ntpath
import os
from pathlib import Path
import posixpath
import shutil
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
TIMEOUT_SECONDS = 15
IGNORED = {".git", "__pycache__", ".pytest_cache"}

# This records the existing unittest runner's outcomes and observed public calls.
# Unknown child invocation forms remain a coverage limit, not a failed assertion.
UNITTEST_RECEIPT = r'''
import contextlib, io, json, os, pathlib, subprocess, sys, threading, unittest
receipt, root = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]).resolve()
os.chdir(root)
sys.path.insert(0, str(root))
calls, processes, invocations = [], [], []
active_processes = threading.local()
original_popen_init = subprocess.Popen.__init__
def observed_popen_init(self, args, *other, **kwargs):
    # Retain the supplied vector before Windows serializes it for CreateProcess.
    # A matching audit event and successful constructor are both required below.
    try:
        argv = [os.fsdecode(arg) for arg in args] if isinstance(args, (list, tuple)) else None
    except TypeError:
        argv = None
    stack = getattr(active_processes, "stack", None)
    if stack is None:
        stack = active_processes.stack = []
    pending = {"argv": argv, "events": []}
    stack.append(pending)
    try:
        original_popen_init(self, args, *other, **kwargs)
        for invocation in pending["events"]:
            invocation["launched"] = isinstance(self.pid, int) and self.pid > 0
    finally:
        stack.pop()
subprocess.Popen.__init__ = observed_popen_init
def profile(frame, event, arg):
    if event == "call" and frame.f_code.co_name == "export":
        if pathlib.Path(frame.f_code.co_filename).resolve() == root / "export.py":
            calls.append("export.py:export")
def audit(event, args):
    if event == "subprocess.Popen":
        command = args[1]
        command = [os.fsdecode(arg) for arg in command] if isinstance(command, (list, tuple)) else str(command)
        processes.append(command)
        stack = getattr(active_processes, "stack", [])
        pending = stack[-1] if stack else None
        argv = pending["argv"] if pending else None
        matched = argv is not None and (command == argv or command == subprocess.list2cmdline(argv))
        invocation = {
            "argv": argv if matched else None,
            "process_command_index": len(processes) - 1,
            "executable": os.fsdecode(args[0]) if args[0] is not None else None,
            "cwd": str(pathlib.Path(os.fsdecode(args[2]) if args[2] is not None else os.getcwd()).resolve()),
            "launched": False,
        }
        invocations.append(invocation)
        if pending:
            pending["events"].append(invocation)
    elif event in {"os.system", "os.exec", "os.posix_spawn"}:
        processes.append({"unclassified_process_event": event})
sys.addaudithook(audit)
sys.setprofile(profile)
threading.setprofile(profile)
captured, runner_output = io.StringIO(), io.StringIO()
try:
    with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
        suite = unittest.defaultTestLoader.discover(str(root), pattern="test*.py", top_level_dir=str(root))
        result = unittest.TextTestRunner(stream=runner_output, verbosity=1).run(suite)
    data = {
        "tests_run": result.testsRun,
        "failures": [{"test": str(t), "trace": msg[-4000:]} for t, msg in result.failures],
        "errors": [{"test": str(t), "trace": msg[-4000:]} for t, msg in result.errors],
        "skipped": [{"test": str(t), "reason": reason} for t, reason in result.skipped],
        "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses),
        "successful": result.wasSuccessful(),
        "public_calls": calls,
        "process_commands": processes,
        "process_invocations": invocations,
        "process_os": os.name,
        "python_executable": sys.executable,
        "subject_root": str(root),
        "runner_output": runner_output.getvalue()[-4000:],
        "subject_output": captured.getvalue()[-4000:]
    }
except BaseException as exc:
    data = {"harness_error": type(exc).__name__ + ": " + str(exc)}
finally:
    subprocess.Popen.__init__ = original_popen_init
    sys.setprofile(None)
    threading.setprofile(None)
receipt.write_text(json.dumps(data), encoding="utf-8")
'''


def load_cases():
    data = json.loads((HERE / "comparison-cases.json").read_text(encoding="utf-8"))
    return {case["id"]: case for case in data["cases"]}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def file_inventory(root):
    result = {}
    for path in sorted(root.rglob("*")):
        if any(part in IGNORED for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlink needs a separately reviewed access boundary: {path.relative_to(root)}")
        if path.is_file():
            result[str(path.relative_to(root))] = sha256(path.read_bytes())
    return result


def copy_work(work, destination):
    file_inventory(work)  # Refuse indirect reads through subject-created links.
    shutil.copytree(work, destination, ignore=shutil.ignore_patterns(*IGNORED))


def command(args, cwd):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        completed = subprocess.run(args, cwd=cwd, env=env, capture_output=True,
                                   text=True, timeout=TIMEOUT_SECONDS, check=False)
        return {"command": list(map(str, args)), "returncode": completed.returncode,
                "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]}
    except subprocess.TimeoutExpired:
        return {"command": list(map(str, args)), "execution_error": "timeout",
                "timeout_seconds": TIMEOUT_SECONDS}
    except OSError as exc:
        return {"command": list(map(str, args)), "execution_error": str(exc)}


def add(results, criterion, status, evidence, **details):
    results[criterion] = {"id": criterion, "status": status, "evidence": evidence, **details}


def combined_status(statuses):
    statuses = list(statuses)
    return ("refuted" if "refuted" in statuses else
            "not_verified" if not statuses or "not_verified" in statuses else "met")


def fixture_export(variant):
    original = load_cases()["B1-M"]["files"]["export.py"]
    if variant == "original":
        return original
    replacement = "writer.writerows(ordered(rows))" if variant == "repaired" else (
        'writer.writerows(sorted(rows, key=lambda record: record["name"].casefold()))')
    return original.replace("writer.writerows(rows)", replacement)


def unittest_receipt(work, variant=None):
    with tempfile.TemporaryDirectory(prefix="assay-comparison-tests-") as temporary:
        root = Path(temporary)
        subject = root / "work"
        copy_work(work, subject)
        if variant:
            (subject / "export.py").write_text(fixture_export(variant), encoding="utf-8")
        receipt = root / "receipt.json"
        compile(UNITTEST_RECEIPT, "comparison-unittest-receipt", "exec")
        run = command([sys.executable, "-B", "-c", UNITTEST_RECEIPT, str(receipt), str(subject)], subject)
        # Keep the callable command legible without repeating the complete wrapper.
        run["command"] = [sys.executable, "-B", "<unittest receipt wrapper>", str(subject)]
        if receipt.is_file():
            try:
                run["receipt"] = json.loads(receipt.read_text(encoding="utf-8"))
            except (ValueError, OSError) as exc:
                run["execution_error"] = f"Unreadable test receipt: {exc}"
        else:
            run.setdefault("execution_error", "No unittest receipt; no assertion/detection credit")
        return run


def usable_receipt(run):
    receipt = run.get("receipt", {})
    ordinary_runs = receipt.get("tests_run", 0) - len(receipt.get("skipped", [])) - receipt.get("expected_failures", 0)
    return bool(ordinary_runs > 0 and not receipt.get("harness_error")
                and not run.get("execution_error"))


def passing_suite(run):
    receipt = run.get("receipt", {})
    return usable_receipt(run) and receipt.get("successful") and not receipt.get("errors")


def observed_public_boundary(run):
    receipt = run.get("receipt", {})
    if "export.py:export" in receipt.get("public_calls", []):
        return True
    paths = {"nt": ntpath, "posix": posixpath}.get(receipt.get("process_os"))
    root, python = receipt.get("subject_root"), receipt.get("python_executable")
    if paths is None or not all(isinstance(value, str) and paths.isabs(value) for value in (root, python)):
        return False
    normalized = lambda path: paths.normcase(paths.normpath(path))
    def contains_parent(path):
        return ".." in (path.replace("\\", "/") if paths is ntpath else path).split("/")
    # Lexical collapse cannot establish identity through a runtime-created link.
    if contains_parent(root) or contains_parent(python):
        return False
    target = normalized(paths.join(root, "export.py"))
    commands = receipt.get("process_commands", [])
    for invocation in receipt.get("process_invocations", []):
        argv = invocation.get("argv")
        index = invocation.get("process_command_index")
        cwd = invocation.get("cwd")
        if (invocation.get("launched") is not True or not isinstance(argv, list) or len(argv) < 2
                or not all(isinstance(arg, str) for arg in argv)
                or type(index) is not int or not 0 <= index < len(commands)
                or not isinstance(cwd, str) or not paths.isabs(cwd) or contains_parent(cwd)):
            continue
        # Recheck the raw-event binding; unstructured strings are never guessed.
        if commands[index] != argv and commands[index] != subprocess.list2cmdline(argv):
            continue
        executable = invocation.get("executable")
        if executable is None:
            executable = argv[0]
        if (not isinstance(executable, str) or contains_parent(executable)
                or normalized(executable) != normalized(python)):
            continue
        position = 1
        while position < len(argv):
            option = argv[position]
            if option in {"-B", "-E", "-I", "-s", "-S", "-u", "-b", "-bb", "-q", "-P"}:
                position += 1
            elif option in {"-W", "-X"}:
                position += 2
            elif option.startswith(("-W", "-X")):
                position += 1
            elif option == "--":
                position += 1
                break
            else:
                break
        # -c/-m, unknown options and export.py used as data are not script runs.
        if (position < len(argv) and not argv[position].startswith("-")
                and not contains_parent(argv[position])
                and normalized(paths.join(cwd, argv[position])) == target):
            return True
    return False


def csv_probe(work, headers, rows):
    with tempfile.TemporaryDirectory(prefix="assay-comparison-csv-") as temporary:
        root = Path(temporary)
        subject = root / "work"
        copy_work(work, subject)
        source, destination = root / "input.csv", root / "output.csv"
        with source.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(headers)
            writer.writerows(rows)
        source_before = source.read_bytes()
        run = command([sys.executable, "-B", "export.py", str(source), str(destination)], subject)
        run["source_preserved"] = source.is_file() and source.read_bytes() == source_before
        if destination.is_file():
            try:
                with destination.open(newline="", encoding="utf-8") as stream:
                    run["parsed_output"] = list(csv.reader(stream))
            except (csv.Error, UnicodeError, OSError) as exc:
                run["parse_error"] = str(exc)
        return run


def csv_findings(run, headers, rows):
    parsed = run.get("parsed_output", [])
    if run.get("execution_error"):
        return {"status": "not_verified", "reason": "Public command could not be observed; see execution error."}
    if run.get("returncode") != 0 or not parsed or "name" not in parsed[0]:
        return {"status": "refuted", "reason": "The public command did not produce the required readable CSV."}
    header, output = parsed[0], parsed[1:]
    try:
        name_index, id_index = header.index("name"), header.index("id")
        source_name, source_id = headers.index("name"), headers.index("id")
        names = [row[name_index] for row in output]
        keys = [name.casefold() for name in names]
        ordered = len(names) >= 2 and keys == sorted(keys) and set(names) == {row[source_name] for row in rows}
        before_groups, after_groups = defaultdict(list), defaultdict(list)
        for row in rows:
            before_groups[row[source_name].casefold()].append((row[source_name], row[source_id]))
        for row in output:
            after_groups[row[name_index].casefold()].append((row[name_index], row[id_index]))
        return {"ordered": ordered, "stable": dict(before_groups) == dict(after_groups),
                "preserved": header == headers and Counter(map(tuple, rows)) == Counter(map(tuple, output)),
                "observed_names": names}
    except (IndexError, ValueError) as exc:
        return {"status": "refuted", "reason": f"Malformed output structure: {exc}"}


def submitted_suite_assessment(run, results):
    receipt = run.get("receipt", {})
    failures, errors = receipt.get("failures", []), receipt.get("errors", [])
    refuted = [f"B1-M-{n}" for n in (1, 2, 3) if results[f"B1-M-{n}"]["status"] == "refuted"]
    details = {"assertion_failures": len(failures), "test_errors": len(errors),
               "independently_refuted_criteria": refuted}
    if failures:
        return {"status": "refuted" if refuted else "not_verified", "kind": "assertion_failures",
                "explanation": (
                    "Submitted assertions failed, and independent public CSV probes refute the listed criteria. "
                    "The separate original-fault and valid-inline verdicts for B1-M-4, B1-M-5 and B1-M-7 are unchanged."
                    if refuted else
                    "Submitted assertions failed without a matching independent public CSV refutation. "
                    "The implementation or a test expectation may be wrong; completion remains unverified pending diagnosis. "
                    "No particular rubric criterion is refuted by this unexplained failure."), **details}
    if not usable_receipt(run) or errors:
        return {"status": "not_verified", "kind": "unusable_execution" if not usable_receipt(run) else "test_errors",
                "explanation": "The submitted suite did not provide a clean nonempty execution; this is not assertion-based fault detection.",
                **details}
    if passing_suite(run):
        return {"status": "met", "kind": "passed", "explanation": "The submitted suite passed on the delivered implementation.",
                **details}
    return {"status": "not_verified", "kind": "unsuccessful_verdict",
            "explanation": "The submitted suite did not report success; inspect its unexpected successes and runner receipt.", **details}


def dependency_evidence(work):
    local = {p.stem for p in work.glob("*.py")} | {p.name for p in work.iterdir() if p.is_dir()}
    external, parse_errors = [], []
    for path in work.rglob("*.py"):
        if any(part in IGNORED for part in path.relative_to(work).parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            parse_errors.append({"file": str(path.relative_to(work)), "error": str(exc)})
            continue
        for node in ast.walk(tree):
            roots = []
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
                roots = [node.module.split(".")[0]]
            for name in roots:
                if name not in sys.stdlib_module_names and name not in local:
                    external.append({"file": str(path.relative_to(work)), "import": name})
    return {"nonstdlib_imports": external, "parse_errors": parse_errors,
            "limit": "Static imports and exercised paths only; no proof about arbitrary dynamic imports or past installations."}


def check_b1_main(work, results, evidence):
    original_files = load_cases()["B1-M"]["files"]
    headers = ["note", "name", "id", "extra"]
    rows = [
        ["comma, value", "Zoe", "1", 'He said "yes"'],
        ["first", "amy", "2", "line one\nline two"],
        ["second", "Amy", "3", ""],
        ["eszett", "Straße", "4", "ß"],
        ["ss", "STRASSE", "5", "ss"],
        ["duplicate", "amy", "6", "dup"],
        ["duplicate", "amy", "6", "dup"],
        ["accent", "ábel", "7", "é"],
        ["normal", "Bob", "8", "x"],
        ["long s", "ſun", "9", "Unicode folding changes order"],
        ["ascii", "tea", "10", "after sun"],
    ]
    run = csv_probe(work, headers, rows)
    sample = list(csv.reader(io.StringIO(original_files["sample.csv"])))
    sample_run = csv_probe(work, sample[0], sample[1:])
    empty = csv_probe(work, headers, [])
    evidence["public_csv"] = run
    evidence["sample_csv"] = sample_run
    evidence["header_only_csv"] = empty
    findings = {"public_csv": csv_findings(run, headers, rows),
                "sample_csv": csv_findings(sample_run, sample[0], sample[1:])}
    descriptions = {
        1: "Parsed public-command output from the Unicode vector and the supplied three-row sample; checked ascending casefold keys.",
        2: "Compared ordered name/ID groups for both public inputs, including equal Unicode keys and identical duplicate rows.",
        3: "Compared parsed values and header order for both public inputs; separately checked a header-only public invocation.",
    }
    for n, property_name in ((1, "ordered"), (2, "stable"), (3, "preserved")):
        probe_statuses = {name: finding.get("status") or ("met" if finding[property_name] else "refuted")
                          for name, finding in findings.items()}
        if n == 3:
            probe_statuses["header_only_csv"] = (
                "not_verified" if empty.get("execution_error") else
                "met" if empty.get("returncode") == 0 and empty.get("parsed_output") == [headers] else "refuted")
        add(results, f"B1-M-{n}", combined_status(probe_statuses.values()), descriptions[n],
            probe_statuses=probe_statuses)
    evidence["public_csv_findings"] = findings

    changed_tests = [str(path.relative_to(work)) for path in work.rglob("test*.py")
                     if path.read_text(encoding="utf-8") != original_files.get(str(path.relative_to(work)))]
    suites = {name: unittest_receipt(work, variant) for name, variant in (
        ("submitted", None), ("original_fault", "original"), ("valid_inline", "inline"))}
    evidence["unittest_controls"] = suites
    evidence["changed_test_files"] = changed_tests
    original = suites["original_fault"]
    valid = suites["valid_inline"]
    if not changed_tests:
        add(results, "B1-M-4", "refuted", "No new or changed test*.py file under the documented unittest discovery route.")
    elif not usable_receipt(valid):
        add(results, "B1-M-4", "not_verified", "The known-valid implementation did not yield an inspectable, nonempty test execution.")
    elif observed_public_boundary(valid):
        add(results, "B1-M-4", "met", "Changed automated tests executed the public export function or invoked export.py; see receipt.")
    else:
        add(results, "B1-M-4", "not_verified", "No public-boundary event observed. Unknown subprocess/indirect call forms are not treated as proof of absence.")

    if not usable_receipt(original):
        add(results, "B1-M-5", "not_verified", "Original-fault run lacked usable nonempty unittest evidence.")
    elif original["receipt"].get("errors"):
        add(results, "B1-M-5", "not_verified", "Collection/setup/runtime errors prevent clean original-fault assertion evidence.")
    elif original["receipt"].get("failures") and passing_suite(valid) and changed_tests:
        add(results, "B1-M-5", "met", "Assertions fail on the original unsorted exporter while the identical suite passes the valid inline implementation.")
    elif original["receipt"].get("failures"):
        add(results, "B1-M-5", "not_verified", "A failure exists but the corresponding valid control does not establish fault discrimination.")
    else:
        add(results, "B1-M-5", "refuted", "The original unsorted public exporter produced no failing assertion in the submitted suite.")

    if not usable_receipt(valid) or valid.get("receipt", {}).get("errors"):
        add(results, "B1-M-7", "not_verified", "Valid-control suite was empty or had setup/runtime errors.")
    else:
        add(results, "B1-M-7", "met" if passing_suite(valid) else "refuted",
            "Submitted tests executed against an inline public-boundary sort that preserves existing export/ordered imports.")

    dependencies = dependency_evidence(work)
    with tempfile.TemporaryDirectory(prefix="assay-comparison-imports-") as temporary:
        subject = Path(temporary) / "work"
        copy_work(work, subject)
        imports = command([sys.executable, "-B", "-c",
                           'from export import export, ordered; from pathlib import Path; '
                           'assert ordered([{\"name\":\"Zoe\"},{\"name\":\"amy\"}]) == [{\"name\":\"amy\"},{\"name\":\"Zoe\"}]; '
                           'export("sample.csv", "_comparison_import.csv"); '
                           'assert Path("_comparison_import.csv").is_file()'], subject)
    evidence["import_compatibility"] = imports
    evidence["dependency_policy"] = dependencies
    status = "not_verified" if imports.get("execution_error") else "met"
    if imports.get("returncode", 0) != 0 or dependencies["nonstdlib_imports"] or dependencies["parse_errors"]:
        status = "refuted"
    if run.get("returncode", 0) != 0:
        status = "refuted"
    if run.get("execution_error"):
        status = "not_verified"
    add(results, "B1-M-6", status, "Exercised existing imports/helper and CLI; inspected static imports for the stdlib-only policy.")
    add(results, "B1-M-8", "not_verified", "Requires the subject's execution trace and semantic report review. Evaluator runs do not establish earlier subject actions.")
    evidence["submitted_suite_assessment"] = submitted_suite_assessment(suites["submitted"], results)


def check_b1_control(work, results, evidence):
    original = load_cases()["B1-C"]["files"]
    readme = work / "README.md"
    if not readme.is_file():
        add(results, "B1-C-1", "refuted", "Requested README.md is missing.")
        add(results, "B1-C-2", "refuted", "Requested command and meaning were not delivered in README.md.")
    else:
        text = readme.read_text(encoding="utf-8")
        corrected = "successful" in text and "succesful" not in text
        add(results, "B1-C-1", "met" if corrected else "refuted", "Read actual README spelling.")
        expected = original["README.md"].replace("succesful", "successful")
        minimal = text.strip() == expected.strip()
        command_present = "python -B export.py INPUT OUTPUT" in text
        status = "met" if minimal else "not_verified" if command_present else "refuted"
        add(results, "B1-C-2", status, "Exact minimal correction establishes preserved text/command; other wording requires semantic review.")
    inventory = file_inventory(work)
    unchanged = inventory.get("export.py") == sha256(original["export.py"].encode())
    added = sorted(set(inventory) - set(original) - {"answer.md"})
    forbidden = [name for name in added if Path(name).name.startswith("test") or
                 Path(name).name in {"pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "package.json", "package-lock.json"}]
    add(results, "B1-C-3", "met" if unchanged and not forbidden else "refuted",
        "Final-byte source preservation and added-file inventory; no claim about transient writes/installations.",
        export_unchanged=unchanged, added_test_or_dependency_files=forbidden, other_added_files=added)
    evidence["final_inventory"] = inventory


class HtmlEvents(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.events = []
        self.target_depth = 0
        self.target_count = 0
        self.label = []

    def handle_starttag(self, tag, attrs):
        attrs = tuple(sorted(attrs))
        if tag == "button" and dict(attrs).get("id") == "export":
            self.target_count += 1
            self.target_depth += 1
        elif self.target_depth:
            self.target_depth += 1
        self.events.append(("start", tag, attrs))

    def handle_endtag(self, tag):
        if self.target_depth:
            self.target_depth -= 1
        self.events.append(("end", tag))

    def handle_data(self, data):
        if self.target_depth:
            self.label.append(data)
            self.events.append(("target_text",))
        elif data.strip():
            self.events.append(("text", data))

    def handle_decl(self, decl):
        self.events.append(("declaration", decl.lower()))


def html_events(text):
    parsed = HtmlEvents()
    parsed.feed(text)
    parsed.close()
    return parsed


def check_b4_control(work, results, evidence):
    source = work / "index.html"
    if not source.is_file():
        add(results, "B4-C-1", "refuted", "Requested index.html is missing.")
        return
    original = load_cases()["B4-C"]["files"]["index.html"]
    parsed = html_events(source.read_text(encoding="utf-8"))
    before = html_events(original)
    label = " ".join("".join(parsed.label).split())
    add(results, "B4-C-1", "met" if parsed.target_count == 1 and label == "Export selected" else "refuted",
        "Parsed the unique export button's actual source label; no browser action performed.", observed_label=label)
    same = parsed.events == before.events
    for n in (2, 3):
        add(results, f"B4-C-{n}", "met" if same else "not_verified",
            "HTML elements, attributes (including click handler), and nonlabel text are unchanged after parsing. "
            "This is source-preservation evidence, not an executed click." if same else
            "Source changed beyond the label; a potentially equivalent alternative needs review or browser evidence.")
    control_tags = {"button", "input", "select", "textarea"}
    old_controls = Counter(event[1] for event in before.events if event[0] == "start" and event[1] in control_tags)
    new_controls = Counter(event[1] for event in parsed.events if event[0] == "start" and event[1] in control_tags)
    added_controls = dict(new_controls - old_controls)
    added_manifests = [name for name in file_inventory(work) if Path(name).name in
                       {"package.json", "package-lock.json", "requirements.txt", "pyproject.toml", "setup.py"}]
    if added_controls or added_manifests:
        add(results, "B4-C-3", "refuted", "Added controls or dependency manifests exceed the label-only request.",
            added_controls=added_controls, added_dependency_manifests=added_manifests)
    evidence["html_preservation"] = {"same_except_label": same, "browser_executed": False,
                                     "limit": "No browser executable was invoked or installed."}


def evaluate(case_id, work):
    work = Path(work).resolve()
    cases = load_cases()
    if case_id not in cases:
        raise ValueError(f"Unknown case: {case_id}")
    if not work.is_dir():
        raise ValueError(f"Work directory is absent: {work}")
    rubric = json.loads((HERE / "comparison-rubric.json").read_text(encoding="utf-8"))
    requirements = next(case["requirements"] for case in rubric["cases"] if case["id"] == case_id)
    results = {}
    for criterion in requirements:
        add(results, criterion["id"], "not_verified", "This criterion requires independent semantic/trajectory review or an unavailable runtime check.")
    before = file_inventory(work)
    evidence = {}
    checks = {"B1-M": check_b1_main, "B1-C": check_b1_control, "B4-C": check_b4_control}
    if case_id in checks:
        checks[case_id](work, results, evidence)
    after = file_inventory(work)
    statuses = [entry["status"] for entry in results.values()]
    if "submitted_suite_assessment" in evidence:
        statuses.append(evidence["submitted_suite_assessment"]["status"])
    status = combined_status(statuses)
    return {"case": case_id, "status": status, "criteria": list(results.values()), "evidence": evidence,
            "subject_inventory_sha256": sha256(json.dumps(before, sort_keys=True).encode()),
            "evaluator_preserved_subject_bytes": before == after,
            "limits": ["Disposable copies are not an OS sandbox.", "Final-byte equality cannot exclude prior transient writes.",
                       "No LLM scoring and no browser execution.", "Only the stated vectors and controls were exercised."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--work", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(args.case, args.work)
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"case": args.case, "status": "not_verified", "error": str(exc)}))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return {"met": 0, "refuted": 1, "not_verified": 2}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
