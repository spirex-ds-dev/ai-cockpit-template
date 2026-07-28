from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from check_instruction_traceability import (
    _archive_entries,
    _audit_contract_evidence_errors,
    _audit_locator_errors,
    _audit_path_errors,
    _audit_reverse_ref_errors,
    _path,
    _resolved_path,
    _validate_archive_integrity,
    main,
    validate_audit,
    validate_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/reference/remediation-instruction-traceability.json"
AUDIT = ROOT / "docs/reference/wi01-wi20-bidirectional-traceability-audit.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def load_audit() -> dict:
    return json.loads(AUDIT.read_text(encoding="utf-8"))


def test_current_wi01_wi20_audit_passes() -> None:
    assert validate_audit(load_audit(), ROOT) == []


def test_audit_requires_exactly_wi01_through_wi20() -> None:
    audit = load_audit()
    audit["workItems"] = audit["workItems"][1:]
    errors = validate_audit(audit, ROOT)
    assert any("audit is missing Work Items: WI-01" in error for error in errors)


def test_audit_rejects_missing_implementation_and_acceptance_paths() -> None:
    audit = load_audit()
    row = audit["workItems"][0]
    row["implementationEvidence"][0]["path"] = "scripts/not-present.py"
    row["acceptanceEvidence"][0]["path"] = "tests/not-present.py"
    errors = validate_audit(audit, ROOT)
    assert any("implementationEvidence[0] path does not exist" in error for error in errors)
    assert any("acceptanceEvidence[0] path does not exist" in error for error in errors)


def test_audit_rejects_archive_triple_mismatch() -> None:
    audit = load_audit()
    row = audit["workItems"][0]
    row["contractEvidence"][0]["summaryPath"] = row["contractEvidence"][0]["contractPath"]
    errors = validate_audit(audit, ROOT)
    assert any("does not match one archive index entry" in error for error in errors)


def test_audit_named_path_requires_exact_disposition() -> None:
    audit = load_audit()
    row = audit["workItems"][9]
    row["implementationEvidence"] = [
        record
        for record in row["implementationEvidence"]
        if record["path"] != "docs/getting-started/installation.md"
    ]
    errors = validate_audit(audit, ROOT)
    assert any(
        "lacks exact implementation evidence: docs/getting-started/installation.md" in error
        for error in errors
    )


def test_audit_rejects_missing_reverse_instruction_reference() -> None:
    audit = load_audit()
    audit["workItems"][0]["implementationEvidence"][0]["instructionRefs"] = []
    errors = validate_audit(audit, ROOT)
    assert any(
        "implementationEvidence[0].instructionRefs must reference this row's evidence" in error
        for error in errors
    )


def test_audit_rejects_duplicate_ownership_without_shared_reason() -> None:
    audit = load_audit()
    first = audit["workItems"][0]["implementationEvidence"][0]
    second = audit["workItems"][1]["implementationEvidence"][0]
    second["path"] = first["path"]
    errors = validate_audit(audit, ROOT)
    assert any("duplicate ownership without sharedEvidenceReason" in error for error in errors)


def test_complete_audit_rejects_open_finding() -> None:
    audit = load_audit()
    audit["status"] = "complete"
    audit["findings"] = [
        {
            "findingId": "AUDIT-TEST-001",
            "workItemId": "WI-01",
            "severity": "high",
            "missingDomain": "acceptance",
            "fact": "test mutation",
            "evidence": ["tests/test_instruction_traceability.py"],
            "status": "open",
            "releaseBlocking": True,
            "correctiveWorkItemId": "",
            "reverification": "not_run",
        }
    ]
    audit["workItems"][0]["status"] = "verified"
    audit["workItems"][0]["findings"] = ["AUDIT-TEST-001"]
    errors = validate_audit(audit, ROOT)
    assert any("verified row contains open findings" in error for error in errors)
    assert "complete audit contains open findings" in errors


def test_audit_rejects_finding_linked_from_the_wrong_work_item() -> None:
    audit = load_audit()
    audit["workItems"][0]["findings"] = ["WI10-AUDIT-001"]
    errors = validate_audit(audit, ROOT)
    assert any("WI-01: finding WI10-AUDIT-001 belongs to WI-10" in error for error in errors)


def test_resolved_finding_requires_indexed_corrective_archive_triple() -> None:
    audit = load_audit()
    finding = audit["findings"][0]
    finding["status"] = "resolved"
    finding["correctiveEvidence"] = {
        "contractPath": (
            ".ai/work-items/archive/2026/"
            "wi10-prompt-first-multiplatform-installation-20260728.contract.json"
        ),
        "summaryPath": (
            ".ai/work-items/archive/2026/"
            "wi10-prompt-first-multiplatform-installation-20260728.summary.json"
        ),
        "manifestPath": ".ai/work-items/archive/2026/not-the-corrective-manifest.json",
    }
    errors = validate_audit(audit, ROOT)
    assert any(
        "correctiveEvidence does not match one archive index entry" in error for error in errors
    )


def test_resolved_finding_rejects_missing_corrective_and_finding_evidence() -> None:
    audit = load_audit()
    audit["findings"][0].pop("correctiveEvidence")
    errors = validate_audit(audit, ROOT)
    assert any("correctiveEvidence must be an archive triple" in error for error in errors)

    audit = load_audit()
    audit["findings"][0]["evidence"] = ["docs/reference/not-present-audit-evidence.md"]
    errors = validate_audit(audit, ROOT)
    assert any("evidence path does not exist" in error for error in errors)


def test_current_traceability_manifest_passes() -> None:
    assert validate_manifest(load_manifest(), ROOT) == []


def test_traceability_rejects_archived_contract_through_active_fallback() -> None:
    manifest = load_manifest()
    manifest["instructions"][0]["contractPaths"] = [
        ".ai/work-items/active/ai-cockpit-comprehensive-review-plan.contract.json"
    ]
    errors = validate_manifest(manifest, ROOT)
    assert any("stale active Contract path" in error for error in errors)


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


def test_cli_fails_when_wi01_wi20_audit_cannot_be_read(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_instruction_traceability.py",
            "--repository",
            str(ROOT),
            "--audit",
            "docs/reference/missing-wi-audit.json",
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


def test_archive_integrity_rejects_unreadable_index_and_invalid_entries(tmp_path: Path) -> None:
    archive_root = tmp_path / ".ai/work-items/archive"
    archive_root.mkdir(parents=True)
    index = archive_root / "index.json"
    index.write_text("{not-json", encoding="utf-8")
    assert any(
        "archive index cannot be read" in error for error in _validate_archive_integrity(tmp_path)
    )

    index.write_text(json.dumps({"entries": {}}), encoding="utf-8")
    assert _validate_archive_integrity(tmp_path) == ["archive index entries must be a list"]

    index.write_text(json.dumps({"entries": ["not-an-object"]}), encoding="utf-8")
    assert _validate_archive_integrity(tmp_path) == ["archive index contains a non-object entry"]


def test_archive_integrity_rejects_missing_paths_and_malformed_manifest(tmp_path: Path) -> None:
    archive = tmp_path / ".ai/work-items/archive/2026"
    archive.mkdir(parents=True)
    manifest = archive / "task.archive-manifest.json"
    manifest.write_text("{not-json", encoding="utf-8")
    (tmp_path / ".ai/work-items/archive/index.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "contractPath": ".ai/work-items/archive/2026/missing.contract.json",
                        "contractSha256": "unused",
                        "summaryPath": ".ai/work-items/archive/2026/missing.summary.json",
                        "summarySha256": "unused",
                        "manifestPath": (".ai/work-items/archive/2026/task.archive-manifest.json"),
                        "manifestSha256": "unused",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    errors = _validate_archive_integrity(tmp_path)
    assert any("archive index contract path does not exist" in error for error in errors)
    assert any("archive index summary path does not exist" in error for error in errors)
    assert any("archive index manifest digest mismatch" in error for error in errors)
    assert any("archive manifest cannot be read" in error for error in errors)


def test_audit_helpers_reject_malformed_path_reverse_and_locator_evidence(
    tmp_path: Path,
) -> None:
    readable = tmp_path / "evidence.md"
    readable.write_text("known locator\n", encoding="utf-8")

    errors, records = _audit_path_errors(
        tmp_path,
        "WI-01",
        "implementationEvidence",
        [None, {"path": ""}, {"path": "missing.md"}, {"path": "evidence.md"}],
    )
    assert any("implementationEvidence[0] must be an object" in error for error in errors)
    assert any("implementationEvidence[1].path must be non-empty" in error for error in errors)
    assert any("implementationEvidence[2] path does not exist" in error for error in errors)
    assert records == [{"path": "missing.md"}, {"path": "evidence.md"}]

    reverse_errors = _audit_reverse_ref_errors(
        "WI-01",
        "implementationEvidence",
        [{"path": "evidence.md", "reason": "", "instructionRefs": [], "planRefs": ["wrong"]}],
        {"instruction"},
        {"plan"},
    )
    assert any(".reason must be non-empty" in error for error in reverse_errors)
    assert any(".instructionRefs must reference" in error for error in reverse_errors)
    assert any(".planRefs must reference" in error for error in reverse_errors)

    locator_errors = _audit_locator_errors(
        tmp_path,
        "WI-01",
        (
            (
                "instructionEvidence",
                [
                    {"path": "evidence.md", "ref": "", "locator": ""},
                    {"path": "evidence.md", "ref": "I1", "locator": "absent locator"},
                    {"path": "missing.md", "ref": "I2", "locator": "ignored"},
                ],
            ),
        ),
    )
    assert any(".ref must be non-empty" in error for error in locator_errors)
    assert any(".locator must be non-empty" in error for error in locator_errors)
    assert any("locator is missing: absent locator" in error for error in locator_errors)


def test_audit_helpers_reject_malformed_contract_archive_relationships(tmp_path: Path) -> None:
    assert _archive_entries(tmp_path) == {}
    assert _audit_contract_evidence_errors(tmp_path, "WI-01", [], {}) == [
        "WI-01: contractEvidence must be a non-empty list"
    ]

    errors = _audit_contract_evidence_errors(
        tmp_path,
        "WI-01",
        [
            None,
            {
                "contractPath": "missing.contract.json",
                "summaryPath": "missing.summary.json",
                "manifestPath": "missing.manifest.json",
            },
        ],
        {},
    )
    assert any("contractEvidence[0] must be an object" in error for error in errors)
    assert sum("path does not exist" in error for error in errors) == 3
    assert any("does not match one archive index entry" in error for error in errors)


def test_resolved_finding_rejects_corrective_work_item_identity_mismatch() -> None:
    audit = load_audit()
    finding = audit["findings"][0]
    finding["correctiveWorkItemId"] = "different-corrective-work-item"
    errors = validate_audit(audit, ROOT)
    assert any(
        "correctiveEvidence does not match one archive index entry" in error for error in errors
    )


def test_resolved_path_requires_exact_or_unique_archive_fallback(tmp_path: Path) -> None:
    archive_2025 = tmp_path / ".ai/work-items/archive/2025"
    archive_2026 = tmp_path / ".ai/work-items/archive/2026"
    archive_2025.mkdir(parents=True)
    archive_2026.mkdir(parents=True)
    archived_name = "task.contract.json"
    (archive_2025 / archived_name).write_text("{}", encoding="utf-8")
    active_path = f".ai/work-items/active/{archived_name}"

    assert _resolved_path(tmp_path, active_path) == archive_2025 / archived_name
    assert _resolved_path(tmp_path, "docs/missing.md") is None

    (archive_2026 / archived_name).write_text("{}", encoding="utf-8")
    assert _resolved_path(tmp_path, active_path) is None


def test_archived_contract_path_rejects_stale_active_manifest_reference(tmp_path: Path):
    archive = tmp_path / ".ai/work-items/archive/2026"
    archive.mkdir(parents=True)
    (archive / "example.contract.json").write_text("{}", encoding="utf-8")
    (tmp_path / "plan.md").write_text("WI-1", encoding="utf-8")
    (archive / "example.summary.json").write_text("{}", encoding="utf-8")
    errors = validate_manifest(
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
    assert any("stale active Contract path" in error for error in errors)
