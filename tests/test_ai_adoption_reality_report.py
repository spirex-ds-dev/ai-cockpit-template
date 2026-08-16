from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest
from ai_adoption_reality_report import (
    CONTROL_IDS,
    build_report,
    main,
    render_markdown,
    repository_template_rows,
    validate_report,
)


def template_rows() -> list[dict[str, object]]:
    return [
        {"id": "installation", "status": "implemented", "claim": "Template installer exists."},
        {
            "id": "calibration",
            "status": "template_only",
            "claim": "Calibration requires adopter execution.",
        },
    ]


def test_report_separates_template_truth_and_missing_adopter_state() -> None:
    report = build_report(template_rows(), {})

    assert report["templateCapabilityTruth"]["rows"] == template_rows()
    assert [item["id"] for item in report["adopterVerification"]["controls"]] == CONTROL_IDS
    assert all(
        item["state"] == "not_configured" for item in report["adopterVerification"]["controls"]
    )
    assert report["readinessClaim"] == "not_claimed"


def test_verified_control_requires_non_template_evidence() -> None:
    controls = {"installation": {"state": "verified", "evidence": ["adopter/install-receipt.json"]}}
    report = build_report(template_rows(), controls)

    item = report["adopterVerification"]["controls"][0]
    assert item["state"] == "verified"
    assert item["evidence"] == ["adopter/install-receipt.json"]
    assert validate_report(report) == []

    with pytest.raises(ValueError, match="template-owned"):
        build_report(
            template_rows(), {"sbom": {"state": "verified", "evidence": [".ai/cockpit/sbom.json"]}}
        )


def test_unknown_external_and_malformed_states_fail_closed() -> None:
    report = build_report(
        template_rows(),
        {
            "hosted_ci": {"state": "external_responsibility", "owner": "provider"},
            "branch_protection": {"state": "unknown", "reason": "provider receipt absent"},
        },
    )
    states = {item["id"]: item["state"] for item in report["adopterVerification"]["controls"]}
    assert states["hosted_ci"] == "external_responsibility"
    assert states["branch_protection"] == "unknown"
    assert report["readinessClaim"] == "not_claimed"

    with pytest.raises(ValueError, match="unsupported adopter state"):
        build_report(template_rows(), {"codeql": {"state": "passed"}})


def test_report_and_markdown_are_deterministic_and_do_not_mutate_input() -> None:
    controls = {"codeql": {"state": "not_configured", "reason": "adopter workflow absent"}}
    original = copy.deepcopy(controls)
    first = build_report(template_rows(), controls)
    second = build_report(template_rows(), controls)

    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert render_markdown(first) == render_markdown(second)
    assert controls == original
    markdown = render_markdown(first)
    assert "Template capability truth" in markdown
    assert "Adopter verification" in markdown
    assert "not_configured" in markdown
    assert "production_sandbox" in markdown


def test_validate_report_rejects_missing_evidence_and_unknown_control() -> None:
    report = build_report(template_rows(), {})
    report["adopterVerification"]["controls"][0]["state"] = "verified"
    report["adopterVerification"]["controls"][0]["evidence"] = []
    assert any("evidence" in issue for issue in validate_report(report))

    report = build_report(template_rows(), {})
    report["adopterVerification"]["controls"].append({"id": "other", "state": "unknown"})
    assert any("unknown control" in issue for issue in validate_report(report))


def test_cli_repository_report_can_be_written(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "report.json"
    markdown = tmp_path / "report.md"
    from ai_adoption_reality_report import write_repository_report

    report = write_repository_report(root, output, markdown)
    assert output.is_file() and markdown.is_file()
    assert json.loads(output.read_text(encoding="utf-8")) == report
    assert "external_responsibility" in markdown.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("evidence", "error"),
    [
        (None, "list of paths"),
        ([""], "non-empty strings"),
        ([1], "non-empty strings"),
        (["templates/release.json"], "template-owned"),
    ],
)
def test_build_rejects_malformed_evidence(evidence: object, error: str) -> None:
    with pytest.raises((TypeError, ValueError), match=error):
        build_report(template_rows(), {"installation": {"state": "verified", "evidence": evidence}})


@pytest.mark.parametrize(
    "rows",
    [
        None,
        [1],
        [{"id": "", "status": "implemented"}],
        [{"id": "same", "status": "implemented"}, {"id": "same", "status": "planned"}],
        [{"id": "bad", "status": "unsupported"}],
    ],
)
def test_build_rejects_malformed_template_rows(rows: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        build_report(rows, {})  # type: ignore[arg-type]


def test_build_covers_optional_metadata_and_invalid_control_shapes() -> None:
    report = build_report(
        template_rows(),
        {
            "installation": {
                "state": "verified",
                "evidence": ["adopter/install.json"],
                "owner": "adopter",
                "reason": "receipt checked",
                "verifiedAt": "2026-08-16T00:00:00Z",
            }
        },
    )
    item = report["adopterVerification"]["controls"][0]
    assert item["owner"] == "adopter"
    assert item["reason"] == "receipt checked"
    assert item["verifiedAt"] == "2026-08-16T00:00:00Z"

    with pytest.raises(TypeError, match="adopter controls must be an object"):
        build_report(template_rows(), None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unknown adopter control"):
        build_report(template_rows(), {"other": {}})
    with pytest.raises(TypeError, match="adopter control must be an object"):
        build_report(template_rows(), {"installation": None})  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="verified adopter control"):
        build_report(template_rows(), {"installation": {"state": "verified"}})
    with pytest.raises(ValueError, match="non-empty string"):
        build_report(template_rows(), {"installation": {"owner": ""}})


def test_validate_and_render_reject_structural_corruption() -> None:
    malformed = {
        "schemaVersion": 2,
        "reportKind": "wrong",
        "templateCapabilityTruth": {"rows": None},
        "adopterVerification": {
            "controls": [{"id": "installation", "state": "bad", "evidence": "x"}, 1]
        },
        "readinessClaim": "ready",
    }
    issues = validate_report(malformed)
    assert any("schemaVersion" in issue for issue in issues)
    assert any("reportKind" in issue for issue in issues)
    assert any("template capability rows" in issue for issue in issues)
    assert any("unsupported adopter state" in issue for issue in issues)
    assert any("evidence must be a list" in issue for issue in issues)
    with pytest.raises(ValueError, match="cannot render invalid"):
        render_markdown(malformed)

    no_section = {
        "schemaVersion": 1,
        "reportKind": "adoption_reality",
        "templateCapabilityTruth": {"rows": []},
    }
    assert any("adopterVerification.controls" in issue for issue in validate_report(no_section))


def test_validate_rejects_malformed_evidence_paths_and_duplicate_controls() -> None:
    report = build_report(template_rows(), {})
    controls = report["adopterVerification"]["controls"]
    controls[0]["state"] = "verified"
    controls[0]["evidence"] = ["", ".ai/cockpit/provenance.json"]
    controls.append({"id": "installation", "state": "unknown", "evidence": []})
    issues = validate_report(report)
    assert any("malformed" in issue for issue in issues)
    assert any("template-owned" in issue for issue in issues)
    assert any("unknown control" in issue for issue in issues)


def test_repository_rows_and_cli_error_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    matrix = tmp_path / "docs" / "reference" / "capability-truth-matrix.json"
    matrix.parent.mkdir(parents=True)
    matrix.write_text(json.dumps({"capabilities": "wrong"}), encoding="utf-8")
    with pytest.raises(TypeError, match="capabilities list"):
        repository_template_rows(tmp_path)

    monkeypatch.setattr(
        sys, "argv", ["ai_adoption_reality_report", "--output", str(tmp_path / "out.json")]
    )
    monkeypatch.setattr(
        "ai_adoption_reality_report.write_repository_report",
        lambda *_args: (_ for _ in ()).throw(ValueError("synthetic failure")),
    )
    assert main() == 1
