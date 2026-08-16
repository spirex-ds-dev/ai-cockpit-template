from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from ai_adoption_reality_report import (
    CONTROL_IDS,
    build_report,
    render_markdown,
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
