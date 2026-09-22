"""Shared application service for CLI and MCP; no native agent execution."""
from __future__ import annotations

import asyncio
import copy
import importlib.metadata
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .cache import Cache, atomic_write, source_lock
from .core import EvidenceError, digest, epoch, number, read_document, validate_snapshot
from .processes import ProcessScope
from .guides import GUIDES, guide_ids
from .providers import SOURCES

# Benchmarks and vendor guides share one registry, one cache mechanism and one
# refresh deadline; only their payload contracts differ.
REGISTRY = {**SOURCES, **GUIDES}
from .routing import TASK_TYPES, brief, build_context, source_ids, validate_request

# Optional caller limits. None of them is required to obtain context, and none
# of them removes a candidate; they annotate the context the caller receives.
PREFERENCES = {"quality_loss_pp", "min_score", "max_cost_usd",
               "max_duration_seconds", "allow_stale", "harness"}


def acquisition_summary(sources, *, offline, matched=True):
    """Describe acquisition separately from the evidence it actually delivered."""
    if offline:
        status = "offline"
        message = ("Network refresh is disabled. Diagnostic replay only; do not use this response for live routing. "
                   "Missing cached data is not evidence that publishers have no measurements. "
                   "Run the configured MCP tool or the same CLI setup without --offline first.")
    elif all(s["availability"] == "missing" for s in sources):
        status = "unavailable"
        message = ("No source data is available. This is not evidence that publishers have no matching measurements. "
                   "Inspect sources[].refresh/error/next_retry_at before retrying.")
    elif any(s["availability"] == "missing" for s in sources):
        status = "partial"
        message = ("Some requested sources are unavailable. The decision uses only available data; "
                   "inspect sources[].availability/refresh/error/next_retry_at for gaps.")
    elif any(s["availability"] == "stale" for s in sources):
        status = "stale"
        message = ("Some source data is stale. Refresh did not establish freshness; "
                   "old data may be used only when allow_stale permits it. Inspect source diagnostics.")
    elif any(s["refresh"] not in ("cached", "updated", "validated_not_modified") for s in sources):
        status = "partial"
        message = ("Cached data is within TTL, but a requested refresh did not complete successfully. "
                   "Inspect source diagnostics; do not report this refresh as successful.")
    else:
        status = "ready"
        message = "All requested sources are loaded and within TTL. This does not imply complete model/effort coverage."
        if not matched:
            message += " Loaded primary data has no matching usable measurements for this request; this is not a download failure."
    return {"data_status": status, "data_message": message,
            "usage": "diagnostic_only" if offline else "routing"}


def default_cache():
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    else:
        root = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    return root / "assay" / "benchmark-evidence"


def ingest(cache, document, observed_at):
    data = validate_snapshot(document)
    source = SOURCES.get(data["source_id"])
    if not source or any(data[k] != source[v] for k, v in (("source_url", "url"), ("version", "version"), ("benchmark", "benchmark"))):
        raise EvidenceError("import must match a registered source URL and revision")
    if epoch(observed_at) > cache.clock() + 60:
        raise EvidenceError("observation date cannot be in the future")
    with source_lock(cache.root / (source["id"] + ".lock")) as acquired:
        if not acquired:
            raise EvidenceError("source is currently being refreshed")
        state = cache.read(source)
        if state.get("last_success_at") and epoch(observed_at) < epoch(state["last_success_at"]):
            raise EvidenceError("refusing to replace newer evidence with an older observation")
        changed_at = state.get("data_changed_at") if state.get("data_hash") == digest(data) else observed_at
        state.update(cache_schema=1, source_fingerprint=digest(source), snapshot=data,
                     data_hash=digest(data), data_changed_at=changed_at,
                     last_attempt_at=observed_at, last_success_at=observed_at,
                     next_retry_at=None, failures=0, error=None, validators={})
        atomic_write(cache.root / (source["id"] + ".json"), state)
        return cache.view(source, state, refresh="imported")


def load_config(path: Path | None):
    if path is None:
        return {}
    config = read_document(path)
    if not isinstance(config, dict) or type(config.get("schema_version")) is not int or config["schema_version"] not in (1, 2):
        raise EvidenceError("configuration requires schema_version=1 or 2")
    allowed = {"schema_version", "client", "preferences", "inventory"}
    if config["schema_version"] == 2:
        allowed.update({"advisor", "policy", "telemetry", "task_evidence"})
    if set(config) - allowed:
        raise EvidenceError("unknown configuration field")
    preferences = config.get("preferences", {})
    if not isinstance(preferences, dict) or set(preferences) - PREFERENCES:
        raise EvidenceError("unknown routing preference")
    inventory = config.get("inventory")
    if inventory is not None and (not isinstance(inventory, dict) or set(inventory) != {"available", "observed_at"}):
        raise EvidenceError("inventory requires available and actual observed_at")
    # Validate preferences even before a live inventory is available. The
    # placeholder is validation-only and never eligible for a recommendation.
    validate_request({"client": config.get("client", "unconfigured"), "task_types": ["implementation"],
                      "available": (inventory or {}).get("available", [{"model": "validation-only", "efforts": ["low"]}]),
                      **preferences})
    if inventory:
        epoch(inventory["observed_at"])
    if config["schema_version"] == 2:
        from .advisor_config import settings
        config.update(settings(config))
    return config


def diagnostics():
    packages = {}
    for name in ("mcp", "playwright"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {"python": __import__("platform").python_version(), "packages": packages,
            "mcp_ready": packages["mcp"] == "2.2.0",
            "browser_installed": packages["playwright"] is not None,
            "browser_launch_checked": False,
            "next_steps": [cmd for missing, cmd in (
                (packages["mcp"] != "2.2.0", "Install scripts/requirements-mcp.txt in the same isolated Python environment."),
                (packages["playwright"] is None, "Install scripts/requirements-browser.txt, then python -m playwright install chromium.")) if missing]}


class RoutingService:
    """One client connection's inventory; shared persistent benchmark cache.

MCP has no API to enumerate its host's models. The caller supplies a confirmed
inventory once per connection, or a dated local inventory is configured. Neither
an unqualified family alias nor the server's own guesses resolve model versions.
"""
    def __init__(self, cache: Cache, *, client="unconfigured", preferences=None, inventory=None,
                 timeout=30, browser=False, offline=False, force=False, clock=time.time, advisor_config=None):
        number(timeout, "timeout_seconds", upper=300)
        if timeout <= 0:
            raise EvidenceError("timeout_seconds must be positive")
        self.cache, self.client, self.timeout = cache, client, timeout
        self.browser, self.offline, self.force, self.clock = browser, offline, force, clock
        self.preferences = copy.deepcopy(preferences or {})
        self._inventory = copy.deepcopy(inventory)
        self._lock = threading.Lock()
        self._advisor_config = copy.deepcopy(advisor_config or {})
        self._advisor_workflow = None

    @property
    def advisor_workflow(self):
        from .advisor_service import AdvisorWorkflow
        if self._advisor_workflow is None:
            self._advisor_workflow = AdvisorWorkflow(self, self._advisor_config)
        return self._advisor_workflow

    async def prepare_routing(self, packets, *, available=None, constraints=None, advisor_route=None, portable=False,
                              task_queries=None, cost_objectives=None):
        return await self.advisor_workflow.prepare_routing(
            packets, available=available, constraints=constraints, advisor_route=advisor_route, portable=portable,
            task_queries=task_queries, cost_objectives=cost_objectives)

    def complete_routing(self, decision_id, advisor_result, *, envelope=None):
        return self.advisor_workflow.complete_routing(decision_id, advisor_result, envelope=envelope)

    def record_routing_outcome(self, decision_id, execution):
        return self.advisor_workflow.record_routing_outcome(decision_id, execution)

    def prepare(self, task_types, *, available=None, constraints=None):
        if not isinstance(task_types, list) or not task_types:
            raise EvidenceError("task_types must be a nonempty list of task types")
        with self._lock:
            prefs = copy.deepcopy(self.preferences)
            if constraints is not None:
                if not isinstance(constraints, dict) or set(constraints) - PREFERENCES:
                    raise EvidenceError("unknown routing constraint")
                prefs.update(copy.deepcopy(constraints))
            inv = self._inventory
            if available is not None:
                from .core import timestamp
                inv = {"available": copy.deepcopy(available), "observed_at": timestamp(self.clock())}
            if inv is None:
                return {"status": "needs_inventory", "required": ["available"],
                        "message": "Pass the current host's model IDs, exact resolved evidence names, and supported efforts once per MCP connection."}
            age = self.clock() - epoch(inv["observed_at"])
            if age < -60 or age >= 86400:
                return {"status": "needs_inventory", "required": ["available"],
                        "message": "The client inventory is old or future-dated. Reconfirm it; it is not a model ranking."}
            request = validate_request({"client": self.client, "task_types": list(task_types),
                                        "available": inv["available"], **prefs})
            # Invalid calls must not poison the connection's remembered state.
            if available is not None:
                self._inventory = inv
            # A one-off constraint applies to this call only. It never becomes a
            # silent policy for the next request on the same connection.
            return copy.deepcopy(request)

    def status(self, selected=None):
        selected = selected or sorted(SOURCES)
        self._validate_sources(selected)
        sources = [self.cache.view(REGISTRY[sid], self.cache.read(REGISTRY[sid]), refresh="not_requested") for sid in selected]
        guides = [self.cache.view(GUIDES[gid], self.cache.read(GUIDES[gid]), refresh="not_requested")
                  for gid in self._guides()[0]]
        with self._lock:
            inv = copy.deepcopy(self._inventory)
        return {"client": self.client, "preferences": copy.deepcopy(self.preferences),
                "advisor": self.advisor_workflow.status(),
                "refresh_mode": "offline" if self.offline else "automatic",
                "guides": brief({"sources": guides})["sources"],
                "inventory": {"configured": inv is not None, "observed_at": inv["observed_at"] if inv else None,
                              "models": len(inv["available"]) if inv else 0},
                "installation": diagnostics(), **brief({"sources": sources})}

    @staticmethod
    def _validate_sources(selected):
        if not isinstance(selected, list) or not selected or any(not isinstance(s, str) or s not in REGISTRY for s in selected):
            raise EvidenceError("select registered benchmark or guide sources")

    def _refresh(self, selected, scope):
        def get(sid):
            source = REGISTRY[sid]
            if scope.cancelled.is_set() or scope.remaining() <= 0:
                return self.cache.view(source, self.cache.read(source), refresh="cancelled" if scope.cancelled.is_set() else "deadline_exceeded")
            try:
                return self.cache.get(source, lambda s, v: scope.fetch(s, v, browser=self.browser),
                                      offline=self.offline, force=self.force)
            except (EvidenceError, OSError) as exc:
                return self.cache.view(source, self.cache.read(source), refresh="failed",
                                       error="local_source_error: " + type(exc).__name__)
        with ThreadPoolExecutor(max_workers=3) as pool:
            return list(pool.map(get, selected))

    async def refresh(self, selected=None):
        selected = selected or sorted(REGISTRY)
        self._validate_sources(selected)
        scope = ProcessScope(self.timeout)
        task = asyncio.create_task(asyncio.to_thread(self._refresh, list(dict.fromkeys(selected)), scope))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            scope.cancel()
            # Wait for local supervisors and cache locks to exit; do not leave
            # refresh running after the MCP call or CLI has been cancelled.
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    continue
            # Retrieve supervisor exceptions without masking cancellation.
            if not task.cancelled():
                task.exception()
            raise
        finally:
            scope.cancel()

    def _guides(self, available=None):
        """Guides for this host; an unresolved client never picks a publisher."""
        for_client = guide_ids(self.client, available)
        return (for_client, "client") if for_client else (guide_ids(available=available), "all_publishers")

    async def context(self, request):
        validate_request(request)
        # Queue primary sources first. Supporting evidence and guidance never
        # consume all the time budget before a required source is attempted.
        primary = [sid for name in request["task_types"] for sid, _ in TASK_TYPES[name]["primary"]]
        selected = list(dict.fromkeys(primary + source_ids(request)))
        guides, scope = self._guides(request["available"])
        fetched = await self.refresh(selected + guides)
        sources = [s for s in fetched if s.get("kind") != "guide"]
        guidance = [s for s in fetched if s.get("kind") == "guide"]
        result = build_context(request, sources, guidance=guidance, guidance_scope=scope)
        matched = any(task["primary_comparisons"] for task in result["tasks"])
        # Acquisition status describes the measurements. A guide that failed to
        # load is reported inside the guidance block, not as missing evidence.
        return {**acquisition_summary(sources, offline=self.offline, matched=matched), **result}

    async def get_routing_context(self, task_types, *, available=None, constraints=None, details=False,
                                  task_query=None, features=None):
        request = self.prepare(task_types, available=available, constraints=constraints)
        if "status" in request:
            return {**request, "data_status": "not_checked", "usage": "setup_required",
                    "data_message": "Source refresh has not run: supply the required connection inputs first."}
        result = await self.context(request)
        if task_query is not None or features is not None:
            from .advice_contracts import candidate_id, validate_packets
            from .core import effort
            packets = validate_packets([{"packet_id": "context", "task_types": task_types, "features": features or {}}])
            candidates = [{"candidate_id": candidate_id(a["model"], effort(e)), "model": a["model"], "effort": effort(e)}
                          for a in request["available"] for e in a["efforts"]]
            result["task_similarity_evidence"] = await self.advisor_workflow.task_evidence.async_summarize(
                packets, candidates, {"context": task_query} if task_query is not None else None)
        # details keeps the raw measured rows; it never reveals a constraint that
        # the normal response withheld.
        return result if details else brief(result)
