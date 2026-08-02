"""Fact-derived, repository-local Work Item Intelligence snapshots.

This module deliberately has no network client and no scheduler.  Commands that
change a Work Item may append a fact; queries only read and validate snapshots.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".ai" / "work-items" / "runtime"
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9_-]{2,127}$")
SECRET = re.compile(r"(password|passwd|secret|token|api[_-]?key|private[_-]?key)", re.IGNORECASE)
LIFECYCLE = (
    "intake",
    "preflight",
    "implementation",
    "verification",
    "review",
    "finish",
    "closure",
    "closed",
)
GOVERNANCE = (
    "draft",
    "not_ready",
    "ready",
    "active",
    "waiting_for_dependency",
    "needs_human_confirmation",
    "blocked",
    "verification_failed",
    "ready_for_review",
    "completed_with_limitations",
    "completed",
    "closing",
    "closed",
    "failed",
    "cancelled",
)
HEALTH = ("not_observed", "active", "idle", "stale", "ended", "unknown")
EXIT = {
    "not_found": 10,
    "unavailable": 11,
    "inconsistent": 12,
    "stale": 13,
    "invalid_query": 20,
    "invalid_data": 30,
    "internal": 40,
}
TERMINAL_CLAIMS = {"completed", "release_ready", "distribution_verified"}


class IntelligenceError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _digest(value: object) -> str:
    return (
        "sha256:"
        + hashlib.sha256(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )


def _safe(value: Any, path: str = "fact") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if SECRET.search(str(key)):
                raise IntelligenceError(
                    "invalid_data", f"secret-like field is forbidden: {path}.{key}"
                )
            _safe(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _safe(child, f"{path}[{index}]")


def paths(work_item: str, *, root: Path = ROOT) -> dict[str, Path]:
    if not IDENTIFIER.fullmatch(work_item):
        raise IntelligenceError("invalid_query", "invalid work item identifier")
    base = root / ".ai" / "work-items" / "runtime" / work_item
    return {
        "base": base,
        "facts": base / "facts.jsonl",
        "status": base / "status.json",
        "activity": base / "activity.json",
        "lock": base / "status.lock",
        "index": base.parent / "index.json",
        "indexLock": base.parent / "index.lock",
    }


@contextmanager
def _exclusive_lock(path: Path, *, timeout_seconds: float = 5.0):
    """Use portable exclusive creation; never silently race an index update."""
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, str(os.getpid()).encode())
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise IntelligenceError(
                    "unavailable", f"runtime write lock is unavailable: {path.name}"
                )
            time.sleep(0.01)
    try:
        yield
    finally:
        os.close(descriptor)
        path.unlink(missing_ok=True)


def read_facts(work_item: str, *, root: Path = ROOT) -> list[dict[str, Any]]:
    source = paths(work_item, root=root)["facts"]
    if not source.exists():
        raise IntelligenceError("not_found", f"runtime facts not found for {work_item}")
    facts: list[dict[str, Any]] = []
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        try:
            fact = json.loads(line)
        except json.JSONDecodeError as exc:
            raise IntelligenceError("invalid_data", f"invalid fact JSON at line {number}") from exc
        if not isinstance(fact, dict):
            raise IntelligenceError("invalid_data", f"fact {number} must be an object")
        if fact.get("workItemId") != work_item or not isinstance(fact.get("factId"), str):
            raise IntelligenceError("invalid_data", f"invalid fact identity at line {number}")
        if any(row["factId"] == fact["factId"] for row in facts):
            raise IntelligenceError("invalid_data", f"duplicate factId: {fact['factId']}")
        _safe(fact)
        facts.append(fact)
    return facts


def append_fact(
    work_item: str, fact_type: str, payload: dict[str, Any], *, root: Path = ROOT
) -> dict[str, Any]:
    if not fact_type or not isinstance(payload, dict):
        raise IntelligenceError("invalid_data", "fact type and object payload are required")
    _safe(payload)
    target = paths(work_item, root=root)
    with _exclusive_lock(target["indexLock"]), _exclusive_lock(target["lock"]):
        return _append_unlocked(work_item, fact_type, payload, root=root)


def _append_unlocked(
    work_item: str, fact_type: str, payload: dict[str, Any], *, root: Path
) -> dict[str, Any]:
    """Append while both the Work Item and shared-index locks are held."""
    target = paths(work_item, root=root)
    existing = read_facts(work_item, root=root) if target["facts"].exists() else []
    sequence = len(existing) + 1
    fact = {
        "factId": f"{work_item}:{sequence}",
        "workItemId": work_item,
        "sequence": sequence,
        "factType": fact_type,
        "occurredAt": _now(),
        "source": "ai-cockpit",
        "payload": payload,
    }
    fact["digest"] = _digest(fact)
    with target["facts"].open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(fact, ensure_ascii=False, sort_keys=True) + "\n")
    _rebuild_unlocked(work_item, root=root)
    return fact


def record_fact_once(
    work_item: str, fact_type: str, payload: dict[str, Any], *, root: Path = ROOT
) -> dict[str, Any] | None:
    """Append an authoritative lifecycle fact once without making it an agent claim."""
    target = paths(work_item, root=root)
    _safe(payload)
    with _exclusive_lock(target["indexLock"]), _exclusive_lock(target["lock"]):
        if target["facts"].exists():
            for fact in read_facts(work_item, root=root):
                if fact["factType"] == fact_type and fact.get("payload") == payload:
                    return None
        return _append_unlocked(work_item, fact_type, payload, root=root)


def _state(
    facts: list[dict[str, Any]],
) -> tuple[str, str, list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    types = [str(row.get("factType")) for row in facts]
    blockers: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    risks: list[dict[str, str]] = []
    claimed = {
        str(row.get("payload", {}).get("claim"))
        for row in facts
        if isinstance(row.get("payload"), dict)
    }
    evidence = {
        str(row.get("payload", {}).get("evidenceKind"))
        for row in facts
        if isinstance(row.get("payload"), dict)
    }
    for claim in claimed & TERMINAL_CLAIMS:
        required = "closure" if claim == "completed" else claim
        if required not in evidence:
            missing.append(
                {
                    "code": "required_evidence_missing",
                    "detail": f"{claim} requires {required} evidence",
                }
            )
    if "verification_failed" in types:
        return "verification", "verification_failed", blockers, missing, risks
    if "human_decision_requested" in types and "human_decision_recorded" not in types:
        blockers.append(
            {"code": "human_decision_pending", "detail": "a human decision is required"}
        )
        return "review", "needs_human_confirmation", blockers, missing, risks
    if "dependency_missing" in types:
        blockers.append(
            {"code": "dependency_missing", "detail": "a declared dependency is unavailable"}
        )
        return "preflight", "waiting_for_dependency", blockers, missing, risks
    if missing:
        return "verification", "blocked", blockers, missing, risks
    if "closed" in types:
        return "closed", "closed", blockers, missing, risks
    if "closure_started" in types:
        return "closure", "closing", blockers, missing, risks
    if "finish_passed" in types:
        return "finish", "ready_for_review", blockers, missing, risks
    if "verification_passed" in types:
        return "review", "ready_for_review", blockers, missing, risks
    if "implementation_started" in types:
        return "implementation", "active", blockers, missing, risks
    if "preflight_ready" in types:
        return "preflight", "ready", blockers, missing, risks
    return "intake", "draft", blockers, missing, risks


def snapshot(work_item: str, facts: list[dict[str, Any]], *, root: Path = ROOT) -> dict[str, Any]:
    phase, governance, blockers, missing, risks = _state(facts)
    activity_path = paths(work_item, root=root)["activity"]
    health = "not_observed"
    activity: dict[str, Any] = {"health": health}
    if activity_path.exists():
        activity = json.loads(activity_path.read_text(encoding="utf-8"))
        health = activity.get("health", "unknown")
        if health not in HEALTH:
            health = "unknown"
        activity["health"] = health
    completed = sum(
        1 for fact in facts if fact["factType"] in {"verification_passed", "finish_passed"}
    )
    dependencies = [
        fact["payload"]
        for fact in facts
        if fact["factType"] in {"dependency_declared", "dependency_missing"}
    ]
    decisions = [
        fact["payload"]
        for fact in facts
        if fact["factType"] in {"human_decision_requested", "human_decision_recorded"}
    ]
    verification = [
        fact["payload"]
        for fact in facts
        if fact["factType"]
        in {"verification_started", "verification_passed", "verification_failed"}
    ]
    actions = {
        name: {"eligible": False, "reasonCodes": ["governance_state"]}
        for name in (
            "start",
            "continue",
            "run_verification",
            "retry",
            "request_human_decision",
            "finish",
            "close",
            "cancel",
        )
    }
    if governance == "draft":
        actions["start"] = {"eligible": True, "reasonCodes": []}
    if governance in {"ready", "active"}:
        actions["continue"] = {"eligible": True, "reasonCodes": []}
    if governance == "active":
        actions["run_verification"] = {"eligible": True, "reasonCodes": []}
    if governance == "ready_for_review":
        actions["finish"] = {"eligible": True, "reasonCodes": []}
    if governance == "closing":
        actions["close"] = {"eligible": True, "reasonCodes": []}
    if governance == "needs_human_confirmation":
        actions["request_human_decision"] = {"eligible": True, "reasonCodes": []}
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "identity": {"workItemId": work_item},
        "status": {
            "lifecyclePhase": phase,
            "governanceState": governance,
            "activityHealth": health,
        },
        "progressFacts": {"factCount": len(facts), "verificationPassCount": completed},
        "blockingReasons": blockers,
        "missingEvidence": missing,
        "dependencies": dependencies,
        "humanDecisions": decisions,
        "risks": risks,
        "verification": {
            "state": "not_run" if not verification else verification[-1].get("result", "observed"),
            "records": verification,
        },
        "actionEligibility": actions,
        "currentActivity": activity,
        "statusVersion": 1,
        "factSequence": len(facts),
        "lastFactId": facts[-1]["factId"] if facts else None,
    }
    result["snapshotDigest"] = _digest(result)
    return result


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def _rebuild_unlocked(work_item: str, *, root: Path = ROOT) -> dict[str, Any]:
    facts = read_facts(work_item, root=root)
    result = snapshot(work_item, facts, root=root)
    target = paths(work_item, root=root)
    _atomic_json(target["status"], result)
    entries = []
    if target["index"].exists():
        try:
            entries = json.loads(target["index"].read_text(encoding="utf-8")).get("entries", [])
        except (OSError, json.JSONDecodeError):
            entries = []
    entries = [entry for entry in entries if entry.get("workItemId") != work_item]
    entries.append(
        {
            "workItemId": work_item,
            "governanceState": result["status"]["governanceState"],
            "activityHealth": result["status"]["activityHealth"],
            "factSequence": result["factSequence"],
            "snapshotDigest": result["snapshotDigest"],
        }
    )
    index = {
        "schemaVersion": 1,
        "indexVersion": int(datetime.now(UTC).timestamp() * 1000),
        "entries": sorted(entries, key=lambda row: row["workItemId"]),
    }
    index["indexDigest"] = _digest(index)
    _atomic_json(target["index"], index)
    return result


def rebuild(work_item: str, *, root: Path = ROOT) -> dict[str, Any]:
    target = paths(work_item, root=root)
    with _exclusive_lock(target["indexLock"]), _exclusive_lock(target["lock"]):
        return _rebuild_unlocked(work_item, root=root)


def read_snapshot(work_item: str, *, root: Path = ROOT) -> dict[str, Any]:
    target = paths(work_item, root=root)["status"]
    if not target.exists():
        raise IntelligenceError("not_found", f"snapshot not found for {work_item}")
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntelligenceError("invalid_data", "snapshot JSON is invalid") from exc
    claimed = value.pop("snapshotDigest", None)
    if claimed != _digest(value):
        raise IntelligenceError("inconsistent", "snapshot digest mismatch; rebuild is required")
    value["snapshotDigest"] = claimed
    return value


def query(
    *,
    work_item: str | None = None,
    state: str | None = None,
    pending_human_decisions: bool = False,
    eligible_action: str | None = None,
    after_index_version: int | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    if work_item:
        return read_snapshot(work_item, root=root)
    index = root / ".ai" / "work-items" / "runtime" / "index.json"
    if not index.exists():
        return {"schemaVersion": 1, "indexVersion": 0, "entries": []}
    try:
        data = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntelligenceError("invalid_data", "runtime index JSON is invalid") from exc
    claimed = data.pop("indexDigest", None)
    if claimed != _digest(data):
        raise IntelligenceError(
            "inconsistent", "runtime index digest mismatch; rebuild is required"
        )
    data["indexDigest"] = claimed
    entries = data.get("entries", [])
    if after_index_version is not None and data.get("indexVersion", 0) <= after_index_version:
        entries = []
    active_dir = root / ".ai" / "work-items" / "active"
    active_ids = {
        path.name.removesuffix(".contract.json") for path in active_dir.glob("*.contract.json")
    }
    selected = []
    for entry in entries:
        if entry.get("workItemId") not in active_ids:
            continue
        if state and entry.get("governanceState") != state:
            continue
        item = read_snapshot(entry["workItemId"], root=root)
        if (
            pending_human_decisions
            and item["status"]["governanceState"] != "needs_human_confirmation"
        ):
            continue
        if eligible_action and not item["actionEligibility"].get(eligible_action, {}).get(
            "eligible"
        ):
            continue
        selected.append(item)
    return {"schemaVersion": 1, "indexVersion": data.get("indexVersion", 0), "entries": selected}


def measure_query_baseline(*, root: Path = ROOT, rounds: int = 10) -> dict[str, Any]:
    """Measure read-only local query latency; no result is persisted."""
    if rounds < 1:
        raise IntelligenceError("invalid_query", "rounds must be positive")
    samples: list[float] = []
    for _ in range(rounds):
        start = time.perf_counter()
        query(root=root)
        samples.append((time.perf_counter() - start) * 1000)
    ordered = sorted(samples)
    return {
        "measurementVersion": 1,
        "rounds": rounds,
        "listActiveQueryMs": {
            "min": round(ordered[0], 3),
            "median": round(ordered[len(ordered) // 2], 3),
            "p95": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 3),
            "max": round(ordered[-1], 3),
        },
    }
