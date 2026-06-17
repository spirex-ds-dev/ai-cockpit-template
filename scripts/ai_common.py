#!/usr/bin/env python3
"""Shared helpers for AI Cockpit scripts."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import shlex
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECKS_PATH = PROJECT_ROOT / ".ai" / "cockpit" / "checks.yaml"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be a JSON object")
    return data


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)


def current_head() -> str:
    result = run_git(["rev-parse", "--verify", "HEAD"])
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def path_fingerprint(path: str) -> str:
    candidate = PROJECT_ROOT / path
    if not candidate.exists():
        return "deleted"
    if not candidate.is_file():
        return "non_file"
    return hashlib.sha256(candidate.read_bytes()).hexdigest()


def _raw_worktree_changes() -> dict[str, str]:
    changes: dict[str, str] = {}
    if current_head():
        result = run_git(["diff", "--name-status", "HEAD"])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        _merge_name_status(changes, result.stdout)
    untracked = run_git(["ls-files", "--others", "--exclude-standard"])
    if untracked.returncode != 0:
        raise RuntimeError(untracked.stderr.strip())
    for path in untracked.stdout.splitlines():
        if path.strip():
            changes[path.strip()] = "A"
    return changes


def _merge_name_status(changes: dict[str, str], output: str) -> None:
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        if status.startswith(("R", "C")) and len(parts) >= 3:
            changes[parts[1]] = "D" if status.startswith("R") else status
            changes[parts[2]] = "A"
        else:
            changes[parts[-1]] = status


def capture_dirty_baseline() -> list[dict[str, str]]:
    return [
        {"path": path, "status": status, "fingerprint": path_fingerprint(path)}
        for path, status in sorted(_raw_worktree_changes().items())
    ]


def active_contract() -> dict[str, Any] | None:
    contracts = sorted((PROJECT_ROOT / ".ai" / "work-items" / "active").glob("*.contract.json"))
    if len(contracts) != 1:
        return None
    try:
        return load_json(contracts[0])
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def _baseline(contract: dict[str, Any] | None = None) -> tuple[str, list[dict[str, str]]]:
    data = contract if contract is not None else active_contract() or {}
    base = os.environ.get("AI_BASE_COMMIT", "").strip() or str(data.get("baseCommit", "")).strip()
    dirty = data.get("baselineDirtyPaths", [])
    return base, [item for item in dirty if isinstance(item, dict)] if isinstance(dirty, list) else []


def changed_name_status(
    contract: dict[str, Any] | None = None, *, ignore_baseline_dirty: bool = False
) -> list[tuple[str, str]]:
    changes: dict[str, str] = {}
    head = current_head()
    base, baseline_dirty = _baseline(contract)
    if base:
        valid = run_git(["rev-parse", "--verify", f"{base}^{{commit}}"])
        if valid.returncode != 0:
            raise RuntimeError(f"baseCommit is not a valid commit: {base}")
        if head:
            result = run_git(["diff", "--name-status", f"{base}...HEAD"])
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip())
            _merge_name_status(changes, result.stdout)
    elif head:
        result = run_git(["diff", "--name-status", "HEAD"])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        _merge_name_status(changes, result.stdout)

    changes.update(_raw_worktree_changes())
    for item in [] if ignore_baseline_dirty else baseline_dirty:
        path = item.get("path")
        fingerprint = item.get("fingerprint")
        if isinstance(path, str) and isinstance(fingerprint, str):
            if path_fingerprint(path) == fingerprint:
                changes.pop(path, None)
            elif path not in changes:
                changes[path] = "D" if not (PROJECT_ROOT / path).exists() else str(item.get("status", "M"))
    return sorted((status, path) for path, status in changes.items())


def changed_paths(contract: dict[str, Any] | None = None, *, ignore_baseline_dirty: bool = False) -> list[str]:
    return [
        path
        for _, path in changed_name_status(contract, ignore_baseline_dirty=ignore_baseline_dirty)
    ]


def matches(pattern: str, path: str) -> bool:
    normalized = pattern.rstrip("/")
    if normalized.endswith("/**"):
        prefix = normalized[:-3]
        return path == prefix or path.startswith(f"{prefix}/")
    if any(ch in normalized for ch in "*?["):
        return fnmatch.fnmatch(path, normalized)
    return path == normalized


def included(path: str, patterns: list[str]) -> bool:
    return any(matches(pattern, path) for pattern in patterns)


def parse_simple_manifest(path: Path) -> dict[str, dict[str, str]]:
    manifest: dict[str, dict[str, str]] = {}
    current: str | None = None
    if not path.exists():
        return manifest
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" ") and stripped.endswith(":"):
            current = stripped[:-1].strip('"')
            manifest[current] = {}
            continue
        if current and line.startswith("  ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            manifest[current][key.strip()] = value.strip().strip('"')
    return manifest


def first_match(path: str, manifest: dict[str, dict[str, str]]) -> tuple[str, dict[str, str]] | None:
    found = [(pattern, data) for pattern, data in manifest.items() if matches(pattern, path)]
    if not found:
        return None
    found.sort(key=lambda item: len(item[0]), reverse=True)
    return found[0]


def simple_yaml_lists(path: Path) -> dict[str, list[str]]:
    """Read list values from a tiny YAML subset used by guard policies."""
    result: dict[str, list[str]] = {}
    if not path.exists():
        return result
    stack: list[str] = []
    current_key: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if stripped.startswith("- ") and current_key:
            result.setdefault(current_key, []).append(stripped[2:].strip().strip('"'))
            continue
        if stripped.endswith(":"):
            key = stripped[:-1].strip('"')
            level = indent // 2
            stack = stack[:level]
            stack.append(key)
            current_key = ".".join(stack)
            continue
        current_key = None
    return result


def simple_yaml_scalars(path: Path) -> dict[str, str]:
    """Read scalar values from the same intentionally small YAML subset."""
    result: dict[str, str] = {}
    stack: list[str] = []
    if not path.exists():
        return result
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if stripped.startswith("- ") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        level = indent // 2
        stack = stack[:level]
        key = key.strip().strip('"')
        if not value.strip():
            stack.append(key)
            continue
        result[".".join([*stack, key])] = value.strip().strip('"')
    return result


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_check_registry(path: Path = CHECKS_PATH) -> dict[str, dict[str, str]]:
    """Parse the checks section of the repository's small YAML check catalog."""
    registry: dict[str, dict[str, str]] = {}
    in_checks = False
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent == 0:
            in_checks = stripped == "checks:"
            current = None
            continue
        if not in_checks:
            continue
        if indent == 2 and stripped.endswith(":"):
            current = stripped[:-1]
            registry[current] = {}
            continue
        if indent == 4 and current and ":" in stripped:
            key, value = stripped.split(":", 1)
            registry[current][key] = value.strip().strip('"')
    return registry


def render_check_command(
    check_id: str,
    *,
    contract_path: str,
    summary_path: str,
    registry_path: Path = CHECKS_PATH,
) -> tuple[str, list[str]]:
    registry = load_check_registry(registry_path)
    definition = registry.get(check_id)
    if not definition:
        raise ValueError(f"verification check is not registered: {check_id}")
    template = definition.get("commandTemplate") or definition.get("command")
    if not template:
        raise ValueError(f"registered check has no command: {check_id}")
    command = template.replace("{contractPath}", contract_path).replace("{summaryPath}", summary_path)
    argv = shlex.split(command)
    if not argv or Path(argv[0]).name not in {"make", "gmake"}:
        raise ValueError(f"registered check must invoke an explicit Make target: {check_id}")
    if len(argv) < 2 or argv[1].startswith("-") or "=" in argv[1]:
        raise ValueError(f"registered check must name a Make target: {check_id}")
    return command, argv


def verification_key(item: dict[str, Any]) -> str:
    check_id = item.get("check")
    if non_empty_string(check_id):
        return check_id.strip()
    command = item.get("command")
    return command.strip() if non_empty_string(command) else ""


def redact_machine_paths(value: str) -> str:
    redacted = value.replace(str(PROJECT_ROOT), "<PROJECT_ROOT>")
    redacted = re.sub(r"/(?:Users|home)/[^/\s]+/(?:[^\s\"']+)", "<LOCAL_PATH>", redacted)
    redacted = re.sub(r"[A-Za-z]:\\Users\\[^\\\s]+\\(?:[^\s\"']+)", "<LOCAL_PATH>", redacted)
    return redacted


def contains_machine_path(value: str) -> bool:
    return redact_machine_paths(value) != value


def redact_machine_paths_in_data(value: Any) -> Any:
    if isinstance(value, str):
        return redact_machine_paths(value)
    if isinstance(value, list):
        return [redact_machine_paths_in_data(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_machine_paths_in_data(item) for key, item in value.items()}
    return value
