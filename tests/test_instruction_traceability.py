from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from check_instruction_traceability import (
    _path,
    _validate_archive_integrity,
    main,
    validate_manifest,
)


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
    manifest = copy.deepcopy(load_manifest())
    instruction = manifest["instructions"][2]
    instruction["implementationEvidence"] = [
        path
        for path in instruction["implementationEvidence"]
        if path != "docs/getting-started/installation.md"
    ]
    instruction["requiredNamedPaths"][0].pop("noChangeRationale", None)
    errors = validate_manifest(manifest, ROOT)
    assert any("required named path lacks implementation evidence" in error for error in errors)


def test_named_path_can_be_satisfied_by_implementation_evidence() -> None:
    manifest = copy.deepcopy(load_manifest())
    instruction = manifest["instructions"][2]
    if "docs/getting-started/installation.md" not in instruction["implementationEvidence"]:
        instruction["implementationEvidence"].append("docs/getting-started/installation.md")
    instruction["requiredNamedPaths"][0].pop("noChangeRationale", None)
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


def test_archive_index_digest_drift_fails_closed(tmp_path: Path):
    archive = tmp_path / ".ai/work-items/archive/2026"
    archive.mkdir(parents=True)
    contract = archive / "task.contract.json"
    summary = archive / "task.summary.json"
    manifest = archive / "task.archive-manifest.json"
    contract.write_text("{}\n", encoding="utf-8")
    summary.write_text("{}\n", encoding="utf-8")
    manifest.write_text(
        json.dumps(
            {
                "contractPath": ".ai/work-items/archive/2026/task.contract.json",
                "summaryPath": ".ai/work-items/archive/2026/task.summary.json",
                "contractSha256": "bad",
                "summarySha256": "bad",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / ".ai/work-items/archive/index.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "contractPath": ".ai/work-items/archive/2026/task.contract.json",
                        "contractSha256": "bad",
                        "summaryPath": ".ai/work-items/archive/2026/task.summary.json",
                        "summarySha256": "bad",
                        "manifestPath": ".ai/work-items/archive/2026/task.archive-manifest.json",
                        "manifestSha256": "bad",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    errors = _validate_archive_integrity(tmp_path)
    assert any("digest mismatch" in error for error in errors)


def test_archived_contract_path_resolves_when_manifest_keeps_active_reference(tmp_path: Path):
    archive = tmp_path / ".ai/work-items/archive/2026"
    archive.mkdir(parents=True)
    (archive / "example.contract.json").write_text("{}", encoding="utf-8")
    (tmp_path / "plan.md").write_text("WI-1", encoding="utf-8")
    (archive / "example.summary.json").write_text("{}", encoding="utf-8")
    assert (
        validate_manifest(
            {
                "schemaVersion": 1,
                "planPath": "plan.md",
                "instructions": [
                    {
                        "id": "I1",
                        "summary": "x",
                        "planWorkItems": ["WI-1"],
                        "contractPaths": [".ai/work-items/active/example.contract.json"],
                        "implementationEvidence": [".ai/work-items/active/example.contract.json"],
                        "acceptanceEvidence": [".ai/work-items/active/example.summary.json"],
                        "verificationCommands": ["make check"],
                    }
                ],
            },
            tmp_path,
        )
        == []
    )
