from __future__ import annotations

import copy
import datetime as dt
import json
from pathlib import Path

from check_deprecated_assets import validate_registry


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/reference/deprecated-assets-registry.json"


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_repository_registry_is_valid() -> None:
    assert validate_registry(ROOT, load_registry(), today=dt.date(2026, 7, 26)) == []


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
