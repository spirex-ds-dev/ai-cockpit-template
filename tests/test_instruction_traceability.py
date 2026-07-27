from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from check_instruction_traceability import _path, main, validate_manifest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/reference/remediation-instruction-traceability.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_current_traceability_manifest_passes() -> None:
    assert validate_manifest(load_manifest(), ROOT) == []


def test_unmapped_instruction_fails_closed() -> None:
    manifest = load_manifest()
    manifest["instructions"][0]["planWorkItems"] = []
    errors = validate_manifest(manifest, ROOT)
    assert any("planWorkItems" in error for error in errors)


def test_missing_acceptance_evidence_fails_closed() -> None:
    manifest = load_manifest()
    manifest["instructions"][1]["acceptanceEvidence"] = ["docs/does-not-exist.md"]
    errors = validate_manifest(manifest, ROOT)
    assert any("acceptanceEvidence path does not exist" in error for error in errors)


def test_named_path_requires_evidence_or_explicit_no_change_rationale() -> None:
    manifest = load_manifest()
    manifest["instructions"][2]["requiredNamedPaths"][0].pop("noChangeRationale")
    errors = validate_manifest(manifest, ROOT)
    assert any("required named path lacks implementation evidence" in error for error in errors)


def test_named_path_can_be_satisfied_by_implementation_evidence() -> None:
    manifest = copy.deepcopy(load_manifest())
    instruction = manifest["instructions"][2]
    instruction["implementationEvidence"].append("docs/getting-started/installation.md")
    instruction["requiredNamedPaths"][0].pop("noChangeRationale")
    assert validate_manifest(manifest, ROOT) == []


def test_path_records_accept_objects_and_reject_other_values() -> None:
    assert _path("docs/example.md") == "docs/example.md"
    assert _path({"path": "docs/example.md"}) == "docs/example.md"
    assert _path({"path": 3}) is None
    assert _path(None) is None


def test_invalid_manifest_shape_fails_closed(tmp_path: Path) -> None:
    manifest = load_manifest()
    manifest["schemaVersion"] = 2
    manifest["planPath"] = "missing-plan.md"
    manifest["instructions"][0]["contractPaths"] = [{"notPath": True}]
    manifest["instructions"][0]["verificationCommands"] = [""]
    errors = validate_manifest(manifest, tmp_path)
    assert any("schemaVersion" in error for error in errors)
    assert any("planPath does not exist" in error for error in errors)
    assert any("invalid path record" in error for error in errors)
    assert any("verificationCommands" in error for error in errors)


def test_invalid_instruction_and_named_path_records_fail_closed() -> None:
    manifest = load_manifest()
    manifest["instructions"].append("not-an-object")
    manifest["instructions"][0]["requiredNamedPaths"] = [{"path": 7}]
    errors = validate_manifest(manifest, ROOT)
    assert any("must be an object" in error for error in errors)
    assert any("requiredNamedPaths contains an invalid record" in error for error in errors)


def test_cli_passes_against_archived_contract_lifecycle(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_instruction_traceability.py", "--repository", str(ROOT)],
    )
    assert main() == 0


def test_cli_fails_when_manifest_cannot_be_read(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_instruction_traceability.py",
            "--repository",
            str(tmp_path),
            "--manifest",
            "missing.json",
        ],
    )
    assert main() == 1
