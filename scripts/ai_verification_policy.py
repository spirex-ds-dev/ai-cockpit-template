"""Pure, deterministic verification selection, caching, and escalation policies."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ai_impact_classifier import classify_path

POLICY_LEVELS = ("light", "standard", "strict")
VERIFICATION_SCOPES = ("focused", "full")
ESCALATION_DOMAINS = frozenset({"release", "workflow", "trust", "installer", "unknown"})


def select_policy(
    stage: str, changed_paths: list[str], *, requested: str | None = None
) -> dict[str, Any]:
    """Select a policy without permitting a caller to downgrade risk."""
    if requested is not None and requested not in POLICY_LEVELS:
        raise ValueError(f"unsupported policy level: {requested}")
    domains = {classify_path(path) for path in changed_paths}
    if stage == "release" or domains & ESCALATION_DOMAINS:
        level = "strict"
    elif stage == "pr" or domains & {"project_code", "dependency", "tests"}:
        level = "standard"
    else:
        level = "light"
    if requested is not None and POLICY_LEVELS.index(requested) > POLICY_LEVELS.index(level):
        level = requested
    scope = "full" if stage == "release" or level in {"standard", "strict"} else "focused"
    return {"level": level, "scope": scope, "stage": stage, "domains": sorted(domains)}


def verification_cache_key(inputs: dict[str, Any]) -> str:
    """Return a content address over every input that can affect verification."""
    required = ("base", "diff", "command", "tool", "dependency", "environment", "config")
    missing = [name for name in required if name not in inputs]
    if missing:
        raise ValueError(f"cache key inputs missing: {', '.join(missing)}")
    canonical = json.dumps(inputs, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def order_checks(graph: dict[str, list[str]]) -> list[str]:
    """Topologically order a check DAG and reject unknown/cyclic dependencies."""
    nodes = set(graph)
    unknown = sorted({dependency for deps in graph.values() for dependency in deps} - nodes)
    if unknown:
        raise ValueError(f"unknown check dependencies: {', '.join(unknown)}")
    ordered: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ValueError("verification check DAG contains a cycle")
        if node in visited:
            return
        visiting.add(node)
        for dependency in sorted(graph[node]):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)
        ordered.append(node)

    for node in sorted(nodes):
        visit(node)
    return ordered


def escalation_reasons(
    changed_paths: list[str],
    *,
    unknown: bool = False,
    injection: bool = False,
    prior_failure: bool = False,
) -> list[str]:
    """Return stable reasons; an empty result never lowers an already strict policy."""
    reasons = sorted({classify_path(path) for path in changed_paths} & ESCALATION_DOMAINS)
    if unknown:
        reasons.append("unknown_input")
    if injection:
        reasons.append("injection_signal")
    if prior_failure:
        reasons.append("test_changed_after_failure")
    return sorted(set(reasons))


def verification_signal(required: list[str], index: dict[str, str]) -> dict[str, Any]:
    missing = [x for x in required if x not in index]
    failed = [x for x in required if index.get(x) == "failed"]
    not_run = [x for x in required if index.get(x) == "not_run"]
    passed = [x for x in required if index.get(x) == "passed"]
    if failed:
        value, evidence = "failed", [f"required verification failed: {', '.join(failed)}"]
    elif missing or not_run:
        detail = []
        if missing:
            detail.append(f"missing: {', '.join(missing)}")
        if not_run:
            detail.append(f"not_run: {', '.join(not_run)}")
        value, evidence = "incomplete", [f"required verification incomplete ({'; '.join(detail)})"]
    else:
        value, evidence = "passed", [f"required verification passed: {len(passed)}/{len(required)}"]
    return {
        "value": value,
        "evidence": evidence,
        "sources": ["contract.verification", "summary.verification"],
        "required": required,
        "passed": passed,
        "failed": failed,
        "missing": missing,
        "not_run": not_run,
    }
