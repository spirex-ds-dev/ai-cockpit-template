#!/usr/bin/env python3
"""Create and validate bounded reusable local Full-quality evidence."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import platform
import subprocess  # nosec B404: fixed Git identity inspection only
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
FINAL_STAGES = {"merge", "convergence", "release"}
EVIDENCE_ONLY_PREFIXES = (".ai/cockpit/", ".ai/work-items/", "target/")


def sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def sha256_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def git(root: Path, *args: str) -> str:
    result = subprocess.run(  # nosec B603 B607: fixed Git executable and command list for local repository identity inspection
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def load_active_base(root: Path) -> str:
    contracts = sorted((root / ".ai/work-items/active").glob("*.contract.json"))
    if len(contracts) == 1:
        data = json.loads(contracts[0].read_text(encoding="utf-8"))
        value = data.get("baseCommit")
        if isinstance(value, str) and value:
            return value
    return "HEAD"


def tracked_and_untracked_paths(root: Path, base: str) -> list[str]:
    paths = set(git(root, "diff", "--name-only", f"{base}...HEAD", "--").splitlines())
    paths.update(git(root, "diff", "--name-only", "--").splitlines())
    paths.update(git(root, "ls-files", "--others", "--exclude-standard").splitlines())
    return sorted(path for path in paths if not path.startswith(EVIDENCE_ONLY_PREFIXES))


def path_digest(root: Path, paths: list[str]) -> str:
    entries: list[dict[str, str]] = []
    for relative in paths:
        path = root / relative
        if path.is_file():
            entries.append({"path": relative, "digest": sha256_bytes(path.read_bytes())})
        else:
            entries.append({"path": relative, "digest": "missing"})
    return sha256_json(entries)


def tree_digest(root: Path, base: str, paths: list[str]) -> str:
    payload = {
        "base": base,
        "head": git(root, "rev-parse", "HEAD").strip(),
        "committed": git(root, "diff", "--binary", f"{base}...HEAD", "--"),
        "working": git(root, "diff", "--binary", "--"),
        "paths": path_digest(root, paths),
    }
    return sha256_json(payload)


def environment_digest(root: Path) -> str:
    files = ("Makefile", "requirements-dev.lock", "requirements-dev.in")
    payload = {
        "python": {"executable": os.path.realpath(sys.executable), "version": sys.version},
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "files": {
            name: sha256_bytes((root / name).read_bytes()) if (root / name).is_file() else "missing"
            for name in files
        },
    }
    return sha256_json(payload)


def quality_state(
    root: Path, *, base: str | None, session_root: Path, profile: str
) -> dict[str, str]:
    resolved_base = base or load_active_base(root)
    paths = tracked_and_untracked_paths(root, resolved_base)
    summary_path = session_root / "summary.json"
    if not summary_path.is_file():
        raise ValueError(f"missing Full quality session summary: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("decision") != "PASS":
        raise ValueError("Full quality session summary is not PASS")
    return {
        "baseCommit": resolved_base,
        "treeDigest": tree_digest(root, resolved_base, paths),
        "changedPathsDigest": path_digest(root, paths),
        "environmentDigest": environment_digest(root),
        "profile": profile,
        "sessionId": session_root.name,
        "summaryDigest": sha256_bytes(summary_path.read_bytes()),
    }


def build_receipt(state: Mapping[str, object]) -> dict[str, object]:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": "reusable_local_full_quality",
        "summaryDecision": "PASS",
        **state,
    }


def active_lock(lock_path: Path) -> bool:
    """Return whether another process currently owns the worktree quality lock."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return False


def load_receipt(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid reusable quality receipt: {exc}") from exc
    if not isinstance(value, dict):
        raise TypeError("invalid reusable quality receipt: object required")
    return value


def validate_receipt(
    receipt: Mapping[str, object], state: Mapping[str, object], *, stage: str
) -> list[str]:
    if stage in FINAL_STAGES:
        return [f"reusable local Full quality evidence is forbidden for {stage}; run fresh quality"]
    if (
        receipt.get("schemaVersion") != SCHEMA_VERSION
        or receipt.get("kind") != "reusable_local_full_quality"
    ):
        return ["receipt schema or kind is invalid"]
    if receipt.get("summaryDecision") != "PASS":
        return ["receipt summaryDecision is not PASS"]
    issues = [field for field, value in state.items() if receipt.get(field) != value]
    return [f"receipt {field} does not match current state" for field in issues]


def capture(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    state = quality_state(
        root, base=args.base, session_root=args.session_root.resolve(), profile=args.profile
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(build_receipt(state), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"reusable Full quality evidence written: {args.output}")
    return 0


def validate(args: argparse.Namespace) -> int:
    if args.stage in FINAL_STAGES:
        print(
            f"reusable local Full quality evidence is forbidden for {args.stage}; run fresh quality",
            file=sys.stderr,
        )
        return 1
    receipt = load_receipt(args.receipt)
    session_id = receipt.get("sessionId")
    if not isinstance(session_id, str) or not session_id:
        print("receipt sessionId is invalid", file=sys.stderr)
        return 1
    root = args.root.resolve()
    if active_lock(root / "target/quality/session.lock"):
        print(
            "Reusable Full quality evidence is invalid: a quality session is active; wait, then retry",
            file=sys.stderr,
        )
        return 1
    state = quality_state(
        root,
        base=args.base,
        session_root=root / "target/quality/sessions" / session_id,
        profile="strict",
    )
    issues = validate_receipt(receipt, state, stage=args.stage)
    if issues:
        print("Reusable Full quality evidence is invalid: " + "; ".join(issues), file=sys.stderr)
        return 1
    print(f"Reusable Full quality evidence is valid for {args.stage} only.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    subparsers = parser.add_subparsers(dest="command", required=True)
    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("--base")
    capture_parser.add_argument("--session-root", type=Path, required=True)
    capture_parser.add_argument("--profile", choices=("strict",), required=True)
    capture_parser.add_argument("--output", type=Path, required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--base")
    validate_parser.add_argument("--receipt", type=Path, required=True)
    validate_parser.add_argument(
        "--stage", choices=("task", "merge", "convergence", "release"), default="task"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return capture(args) if args.command == "capture" else validate(args)
    except ValueError as exc:
        print(f"Reusable Full quality evidence is invalid: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
