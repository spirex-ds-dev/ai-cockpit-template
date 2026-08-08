"""Regression coverage for merge-safe generated lifecycle projections."""

from __future__ import annotations

import subprocess
from pathlib import Path

import ai_close_work_item as closure
import ai_projection_lease as lease
import pytest
from ai_check_work_item import validate_concurrency_boundary
from ai_start import (
    LinkedWorktreeIdentity,
    linked_worktree_boundary_issue,
    parse_concurrency_boundary,
)
from ai_start_receipt import build_receipt, receipt_binding, validate_receipt


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=check)


def _commit(root: Path, path: str, text: str, message: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    _git(root, "add", path)
    _git(root, "commit", "-m", message)


def _repository(tmp_path: Path) -> Path:
    origin = tmp_path / "origin.git"
    root = tmp_path / "repository"
    _git(tmp_path, "init", "--bare", str(origin))
    _git(tmp_path, "clone", str(origin), str(root))
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "switch", "-c", "main")
    for path in sorted(lease.BRANCH_INTEGRATED_GENERATED_PATHS):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("base\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "seed")
    _git(root, "push", "-u", "origin", "main")
    return root


def _worktree(root: Path, destination: Path, task: str) -> Path:
    _git(root, "worktree", "add", "-b", f"codex/{task}", str(destination), "origin/main")
    _git(destination, "config", "user.name", "Test")
    _git(destination, "config", "user.email", "test@example.com")
    return destination


def test_projection_inventory_is_closed_and_explicit() -> None:
    inventory = lease.inventory()
    assert inventory["schemaVersion"] == 1
    assert set(inventory["serialized"]) == lease.BRANCH_INTEGRATED_GENERATED_PATHS
    assert ".ai/cockpit/current_status.md" in inventory["serialized"]
    assert ".ai/work-items/archive/index.json" in inventory["serialized"]


def test_parallel_boundary_and_start_receipt_bind_the_exact_inventory(tmp_path: Path) -> None:
    boundary = {
        "schemaVersion": 1,
        "implementationPaths": ["scripts/example.py"],
        "generatedEvidencePaths": ["docs/example.md"],
        "verificationOutputPaths": ["target/quality/example/**"],
        "serializedProjectionPaths": sorted(lease.BRANCH_INTEGRATED_GENERATED_PATHS),
        "reason": "fixture ownership",
    }
    contract = {
        "workItemId": "example",
        "contractVersion": 2,
        "mode": "code",
        "title": "Example",
        "scope": ["scripts/example.py"],
        "baseCommit": "a" * 40,
        "concurrencyBoundary": boundary,
    }
    assert validate_concurrency_boundary(contract) == []
    parsed, error = parse_concurrency_boundary(__import__("json").dumps(boundary), "example")
    assert error is None and parsed == boundary

    root = _repository(tmp_path)
    receipt = build_receipt(contract, project_root=root, timestamp="2026-08-08T00:00:00+00:00")
    contract["startReceipt"] = receipt_binding(receipt)
    assert receipt["concurrencyBoundaryDigest"]
    assert validate_receipt(contract, receipt, project_root=root, require_tracked=False) == []

    boundary["serializedProjectionPaths"] = [".ai/cockpit/current_status.md"]
    assert any(
        "closed branch-integrated projection inventory" in issue
        for issue in validate_concurrency_boundary(contract)
    )


def test_closure_releases_only_an_explicit_parallel_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract_path = tmp_path / "parallel.contract.json"
    contract_path.write_text(
        '{"workItemId":"parallel","concurrencyBoundary":{"schemaVersion":1}}',
        encoding="utf-8",
    )
    released: list[tuple[str, str]] = []
    monkeypatch.setattr(
        closure,
        "release_projection_lease",
        lambda task, branch, **_kwargs: released.append((task, branch)),
    )
    closure._release_projection_lease_if_required("parallel", "codex/parallel", contract_path)
    assert released == [("parallel", "codex/parallel")]


def test_linked_start_rejects_missing_or_overlapping_boundary(tmp_path: Path) -> None:
    worktree = tmp_path / "foreign"
    active = worktree / ".ai/work-items/active"
    active.mkdir(parents=True)
    foreign = {
        "workItemId": "foreign",
        "concurrencyBoundary": {
            "schemaVersion": 1,
            "implementationPaths": ["scripts/foreign.py"],
            "generatedEvidencePaths": ["docs/foreign.md"],
            "verificationOutputPaths": ["target/quality/foreign/**"],
            "serializedProjectionPaths": sorted(lease.BRANCH_INTEGRATED_GENERATED_PATHS),
            "reason": "foreign fixture",
        },
    }
    (active / "foreign.contract.json").write_text(
        __import__("json").dumps(foreign), encoding="utf-8"
    )
    identity = LinkedWorktreeIdentity(worktree, "codex/foreign", "foreign")
    assert "supply a valid --concurrency-boundary" in str(
        linked_worktree_boundary_issue([identity], None, require_boundary=True)
    )

    candidate = dict(foreign["concurrencyBoundary"])
    candidate["implementationPaths"] = ["scripts/foreign.py"]
    assert "overlaps linked Work Item foreign" in str(
        linked_worktree_boundary_issue([identity], candidate, require_boundary=True)
    )


def test_real_linked_worktrees_serialize_projection_writes_until_merge_refresh(
    tmp_path: Path,
) -> None:
    root = _repository(tmp_path)
    first = _worktree(root, tmp_path / "first", "first")
    second = _worktree(root, tmp_path / "second", "second")

    owner = lease.acquire("first", root=first)
    assert owner.task == "first"
    _commit(first, ".ai/cockpit/current_status.md", "first finalized\n", "first projection")

    with pytest.raises(lease.ProjectionLeaseError, match="owned by first"):
        lease.acquire("second", root=second)

    _git(root, "merge", "--no-ff", "codex/first", "-m", "merge first")
    _git(root, "push", "origin", "main")
    lease.release("first", "codex/first", root=first)

    with pytest.raises(lease.ProjectionLeaseError, match="latest origin/main"):
        lease.acquire("second", root=second)
    _git(second, "rebase", "origin/main")
    owner = lease.acquire("second", root=second)
    assert owner.task == "second"
    _commit(second, ".ai/cockpit/current_status.md", "second finalized\n", "second projection")
    _git(root, "merge", "--no-ff", "codex/second", "-m", "merge second")
    assert (root / ".ai/cockpit/current_status.md").read_text(
        encoding="utf-8"
    ) == "second finalized\n"


def test_malformed_lease_fails_closed_without_deleting_evidence(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    worktree = _worktree(root, tmp_path / "task", "task")
    path = lease.lease_path(root=worktree)
    path.write_text("not-json\n", encoding="utf-8")

    with pytest.raises(lease.ProjectionLeaseError, match="unreadable"):
        lease.acquire("task", root=worktree)
    assert path.read_text(encoding="utf-8") == "not-json\n"
