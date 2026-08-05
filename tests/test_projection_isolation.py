"""Regression coverage for merge-safe generated lifecycle projections."""

from __future__ import annotations

import subprocess
from pathlib import Path

import ai_close_work_item as closure
import ai_projection_lease as lease
import pytest
from ai_check_work_item import validate_concurrency_boundary
from ai_start import LinkedWorktreeIdentity, linked_worktree_boundary_issue


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=check)


def _commit(root: Path, path: str, text: str, message: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    _git(root, "add", path)
    _git(root, "commit", "-m", message)


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    origin = tmp_path / "origin.git"
    root = tmp_path / "repository"
    _git(tmp_path, "init", "--bare", str(origin))
    _git(tmp_path, "clone", str(origin), str(root))
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "switch", "-c", "main")
    for path in sorted(lease.BRANCH_INTEGRATED_GENERATED_PATHS):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text("base\n", encoding="utf-8")
    (root / "independent").mkdir(parents=True, exist_ok=True)
    (root / "independent/base.txt").write_text("base\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "seed")
    _git(root, "push", "-u", "origin", "main")
    return root, origin


def _worktree(root: Path, destination: Path, task: str) -> Path:
    _git(root, "worktree", "add", "-b", f"codex/{task}", str(destination), "origin/main")
    _git(destination, "config", "user.name", "Test")
    _git(destination, "config", "user.email", "test@example.com")
    return destination


def test_shared_projection_inventory_is_closed_and_explicit() -> None:
    inventory = lease.inventory()
    assert inventory["schemaVersion"] == 1
    assert set(inventory["serialized"]) == lease.BRANCH_INTEGRATED_GENERATED_PATHS
    assert ".ai/cockpit/current_status.md" in inventory["serialized"]
    assert ".ai/work-items/archive/index.json" in inventory["serialized"]


def test_concurrency_boundary_must_exactly_declare_shared_projection_inventory() -> None:
    boundary = {
        "schemaVersion": 1,
        "implementationPaths": ["scripts/example.py"],
        "generatedEvidencePaths": ["docs/example.md"],
        "verificationOutputPaths": ["target/quality/example/**"],
        "serializedProjectionPaths": sorted(lease.BRANCH_INTEGRATED_GENERATED_PATHS),
        "reason": "fixture ownership",
    }
    contract = {"workItemId": "example", "concurrencyBoundary": boundary}
    assert validate_concurrency_boundary(contract) == []

    boundary["serializedProjectionPaths"] = [".ai/cockpit/current_status.md"]
    issues = validate_concurrency_boundary(contract)
    assert any("closed branch-integrated projection inventory" in issue for issue in issues)


def test_serial_work_item_does_not_require_parallel_boundary() -> None:
    identity = LinkedWorktreeIdentity(Path("/fixture"), "codex/other", "other")
    assert linked_worktree_boundary_issue([identity], None, require_boundary=False) is None
    assert "supply a valid --concurrency-boundary" in str(
        linked_worktree_boundary_issue([identity], None, require_boundary=True)
    )
    assert lease.requires_lease({"workItemId": "legacy"}) is False


def test_explicit_parallel_contract_requires_dedicated_branch_lease(tmp_path: Path) -> None:
    root, _origin = _repository(tmp_path)
    parallel = {
        "workItemId": "parallel",
        "concurrencyBoundary": {
            "serializedProjectionPaths": sorted(lease.BRANCH_INTEGRATED_GENERATED_PATHS)
        },
    }
    assert lease.requires_lease(parallel) is True
    with pytest.raises(lease.ProjectionLeaseError, match="requires codex/parallel"):
        lease.acquire("parallel", root=root)

    worktree = _worktree(root, tmp_path / "parallel", "parallel")
    assert lease.acquire("parallel", root=worktree).task == "parallel"
    with pytest.raises(lease.ProjectionLeaseError, match="cannot release"):
        lease.release("other", "codex/other", root=worktree)


def test_legacy_closure_does_not_release_a_foreign_projection_lease(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = tmp_path / "legacy.contract.json"
    contract.write_text('{"workItemId":"legacy"}', encoding="utf-8")
    released: list[tuple[str, str]] = []
    monkeypatch.setattr(
        closure,
        "release_projection_lease",
        lambda task, branch, **_kwargs: released.append((task, branch)),
    )
    closure._release_projection_lease_if_required("legacy", "codex/legacy", contract)
    assert released == []


def test_parallel_closure_releases_exact_lease_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = tmp_path / "parallel.contract.json"
    contract.write_text(
        '{"workItemId":"parallel","concurrencyBoundary":{"schemaVersion":1}}',
        encoding="utf-8",
    )
    released: list[tuple[str, str]] = []
    monkeypatch.setattr(
        closure,
        "release_projection_lease",
        lambda task, branch, **_kwargs: released.append((task, branch)),
    )
    closure._release_projection_lease_if_required("parallel", "codex/parallel", contract)
    assert released == [("parallel", "codex/parallel")]


def test_real_linked_worktrees_serialize_projection_writes_until_merge_refresh(
    tmp_path: Path,
) -> None:
    root, _origin = _repository(tmp_path)
    first = _worktree(root, tmp_path / "first", "first")
    second = _worktree(root, tmp_path / "second", "second")

    _commit(first, "independent/first.txt", "first\n", "first independent change")
    owner = lease.acquire("first", root=first)
    assert owner.task == "first"
    _commit(first, ".ai/cockpit/current_status.md", "first finalized\n", "first projection")

    _commit(second, "independent/second.txt", "second\n", "second independent change")
    stale_status = (second / ".ai/cockpit/current_status.md").read_text(encoding="utf-8")
    with pytest.raises(lease.ProjectionLeaseError, match="owned by first"):
        lease.acquire("second", root=second)
    assert (second / ".ai/cockpit/current_status.md").read_text(encoding="utf-8") == stale_status

    _git(root, "merge", "--no-ff", "codex/first", "-m", "merge first")
    _git(root, "push", "origin", "main")
    lease.release("first", "codex/first", root=first)

    _git(second, "rebase", "origin/main")
    owner = lease.acquire("second", root=second)
    assert owner.task == "second"
    _commit(second, ".ai/cockpit/current_status.md", "second finalized\n", "second projection")
    _git(root, "merge", "--no-ff", "codex/second", "-m", "merge second")
    assert (root / ".ai/cockpit/current_status.md").read_text(
        encoding="utf-8"
    ) == "second finalized\n"


def test_stale_worktree_cannot_acquire_after_previous_projection_owner_closes(
    tmp_path: Path,
) -> None:
    root, _origin = _repository(tmp_path)
    first = _worktree(root, tmp_path / "first", "first")
    second = _worktree(root, tmp_path / "second", "second")

    lease.acquire("first", root=first)
    _commit(first, ".ai/work-items/archive/index.json", "first index\n", "first archive index")
    _git(root, "merge", "--no-ff", "codex/first", "-m", "merge first")
    _git(root, "push", "origin", "main")
    lease.release("first", "codex/first", root=first)

    with pytest.raises(lease.ProjectionLeaseError, match="latest origin/main"):
        lease.acquire("second", root=second)
    assert (second / ".ai/work-items/archive/index.json").read_text(encoding="utf-8") == "base\n"


def test_malformed_foreign_lease_fails_closed_without_deleting_evidence(tmp_path: Path) -> None:
    root, _origin = _repository(tmp_path)
    worktree = _worktree(root, tmp_path / "task", "task")
    path = lease.lease_path(root=worktree)
    path.write_text("not-json\n", encoding="utf-8")

    with pytest.raises(lease.ProjectionLeaseError, match="unreadable"):
        lease.acquire("task", root=worktree)
    assert path.read_text(encoding="utf-8") == "not-json\n"
