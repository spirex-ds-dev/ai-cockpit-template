from __future__ import annotations

import copy
import datetime as dt
import json
from pathlib import Path

from check_deprecated_assets import validate_current_facing_paths, validate_registry

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/reference/deprecated-assets-registry.json"


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_repository_registry_is_valid() -> None:
    assert validate_registry(ROOT, load_registry(), today=dt.date(2026, 8, 6)) == []


def test_missing_required_field_fails_closed() -> None:
    payload = load_registry()
    del payload["entries"][0]["replacement"]
    assert any("missing replacement" in issue for issue in validate_registry(ROOT, payload))


def test_stale_planned_removal_requires_runtime_false() -> None:
    payload = load_registry()
    payload["entries"][0]["plannedRemoval"] = "2020-01-01"
    payload["entries"][0]["runtimeUsed"] = True
    assert any("stale plannedRemoval" in issue for issue in validate_registry(ROOT, payload))


def test_protected_archive_path_cannot_be_deletable(tmp_path: Path) -> None:
    protected = tmp_path / ".ai/work-items/archive/evidence.json"
    protected.parent.mkdir(parents=True)
    protected.write_text("{}", encoding="utf-8")
    replacement = tmp_path / "replacement.md"
    replacement.write_text("replacement", encoding="utf-8")
    payload = {
        "schemaVersion": 1,
        "entries": [
            {
                "id": "protected",
                "path": ".ai/work-items/archive/evidence.json",
                "type": "archive",
                "replacement": "replacement.md",
                "deprecatedSince": "2026-01-01",
                "plannedRemoval": "never",
                "reason": "test",
                "currentReferences": [],
                "runtimeUsed": False,
                "migrationRequired": False,
                "protected": True,
                "deletionAllowed": True,
            }
        ],
    }
    assert any("deletionAllowed=false" in issue for issue in validate_registry(tmp_path, payload))


def test_validation_does_not_mutate_payload() -> None:
    payload = load_registry()
    original = copy.deepcopy(payload)
    validate_registry(ROOT, payload)
    assert payload == original


def test_current_facing_scan_rejects_reintroduced_obsolete_lifecycle_chain(tmp_path: Path) -> None:
    payload = load_registry()
    payload["currentFacingScan"]["paths"] = ["docs"]
    guide = tmp_path / "docs" / "guide.md"
    guide.parent.mkdir(parents=True)
    guide.write_text(
        "Run `make quality && make staging && make ai-finish TASK=example`.", encoding="utf-8"
    )
    assert validate_current_facing_paths(tmp_path, payload) == [
        "obsolete-quality-staging-finish-chain: docs/guide.md matches prohibited command chain"
    ]


def test_current_facing_scan_rejects_reintroduced_workflow_chain(tmp_path: Path) -> None:
    payload = load_registry()
    payload["currentFacingScan"]["paths"] = [".github/workflows"]
    workflow = tmp_path / ".github" / "workflows" / "obsolete.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "run: make quality && make staging && make ai-finish TASK=example\n", encoding="utf-8"
    )
    assert validate_current_facing_paths(tmp_path, payload) == [
        "obsolete-quality-staging-finish-chain: .github/workflows/obsolete.yml matches prohibited command chain"
    ]


def test_current_facing_scan_excludes_immutable_archive_history(tmp_path: Path) -> None:
    payload = load_registry()
    payload["currentFacingScan"]["paths"] = [".ai"]
    archive = tmp_path / ".ai" / "work-items" / "archive" / "2026" / "history.md"
    archive.parent.mkdir(parents=True)
    archive.write_text(
        "Run `make quality && make staging && make ai-finish TASK=example`.", encoding="utf-8"
    )
    assert validate_current_facing_paths(tmp_path, payload) == []


def test_current_facing_scan_ignores_binary_and_interpreter_cache_files(tmp_path: Path) -> None:
    payload = load_registry()
    payload["currentFacingScan"]["paths"] = ["docs", "scripts"]
    asset = tmp_path / "docs" / "asset.gif"
    cache = tmp_path / "scripts" / "__pycache__" / "validator.pyc"
    asset.parent.mkdir(parents=True)
    cache.parent.mkdir(parents=True)
    asset.write_bytes(b"GIF89a\x00\xff")
    cache.write_bytes(b"\x00\xff")
    assert validate_current_facing_paths(tmp_path, payload) == []


def test_current_facing_scan_fails_closed_for_a_missing_scan_root(tmp_path: Path) -> None:
    payload = load_registry()
    assert validate_current_facing_paths(tmp_path, payload) == [
        "currentFacingScan path does not exist: AGENTS.md",
        "currentFacingScan path does not exist: README.md",
        "currentFacingScan path does not exist: .ai/cockpit",
        "currentFacingScan path does not exist: docs",
        "currentFacingScan path does not exist: Makefile",
        "currentFacingScan path does not exist: scripts",
        "currentFacingScan path does not exist: install.sh",
        "currentFacingScan path does not exist: templates",
        "currentFacingScan path does not exist: .github/workflows",
    ]


def test_missing_current_facing_scan_configuration_fails_closed() -> None:
    payload = load_registry()
    del payload["currentFacingScan"]["prohibitedCommandChains"]
    assert validate_registry(ROOT, payload, today=dt.date(2026, 8, 6)) == [
        "currentFacingScan missing prohibitedCommandChains",
        "currentFacingScan prohibitedCommandChains must be a non-empty list",
    ]
