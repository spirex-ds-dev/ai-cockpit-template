import json
import sys

import ai_japanese_capability
from ai_japanese_capability import (
    CORPUS_PATH,
    evaluate,
    render_json,
    render_markdown,
    report_drift,
)


EXPECTED_FINDINGS = {
    "JA-PR-001": "japanese-pr-output-corrective-20260729",
    "JA-LIFECYCLE-001": "japanese-lifecycle-fixture-corrective-20260729",
    "JA-DOC-001": "japanese-uninstall-documentation-corrective-20260729",
}


def test_status_capability_requires_generator_checker_make_and_executable_parity(
    tmp_path, monkeypatch
):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts/ai_generate_status.py").write_text(
        'STATUS_LANGUAGE = "--language"\n日本語 = True\n',
        encoding="utf-8",
    )
    (tmp_path / "scripts/ai_check_status.py").write_text(
        'STATUS_LANGUAGE = "--language"\n',
        encoding="utf-8",
    )
    (tmp_path / "Makefile").write_text(
        "generate-cockpit-status-ja:\ncheck-ai-status-ja:\n",
        encoding="utf-8",
    )
    (tmp_path / "tests/test_guards_and_status.py").write_text(
        "def test_japanese_status_projection_localizes_chrome_and_preserves_machine_values(): pass\n",
        encoding="utf-8",
    )
    (tmp_path / "tests/test_core_gates.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(ai_japanese_capability, "ROOT", tmp_path)

    assert ai_japanese_capability._status_has_japanese_view() is False

    (tmp_path / "tests/test_core_gates.py").write_text(
        "def test_status_check_rejects_stale_japanese_projection(): pass\n",
        encoding="utf-8",
    )
    assert ai_japanese_capability._status_has_japanese_view() is True


def test_wizard_capability_requires_both_entrypoints_and_executable_tests(tmp_path, monkeypatch):
    scripts = tmp_path / "scripts"
    tests = tmp_path / "tests"
    scripts.mkdir()
    tests.mkdir()
    localization_import = (
        'from ai_wizard_localization import load_messages\nLANGUAGE_OPTION = "--language"\n'
    )
    (scripts / "ai_install_wizard.py").write_text(localization_import, encoding="utf-8")
    (scripts / "ai_calibration_wizard.py").write_text("", encoding="utf-8")
    (tests / "test_install_wizard.py").write_text(
        "def test_japanese_dry_run_uses_executable_locale_resources(): pass\n",
        encoding="utf-8",
    )
    (tests / "test_calibration_wizard.py").write_text(
        "def test_japanese_render_and_pause_use_executable_locale_resources(): pass\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_japanese_capability, "ROOT", tmp_path)

    assert ai_japanese_capability._wizard_is_executable() is False

    (scripts / "ai_calibration_wizard.py").write_text(localization_import, encoding="utf-8")
    assert ai_japanese_capability._wizard_is_executable() is True


def test_independent_corpus_covers_every_required_japanese_input_domain():
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))

    assert corpus["corpusVersion"] == 1
    assert {entry["category"] for entry in corpus["entries"]} == {
        "polite",
        "plain",
        "technical_mixed",
        "markdown",
        "hidden_html",
        "log",
        "tool",
        "injection",
        "base64",
        "unicode_control",
        "nested_quote",
        "unknown_human_confirmation",
        "japanese_path",
        "absurd_high_risk",
    }
    assert all(entry["content"] for entry in corpus["entries"])


def test_comprehensive_matrix_is_evidence_bound_and_reports_current_blockers():
    result = evaluate()

    assert result["assessmentVersion"] == 2
    assert result["scope"] == "bounded repository-governance Japanese handling"
    assert len(result["cases"]) >= 10
    for case in result["cases"]:
        assert {
            "id",
            "area",
            "status",
            "observation",
            "sourceEvidence",
            "testEvidence",
            "commandEvidence",
            "limitation",
            "digest",
        } <= case.keys()
        assert case["digest"].startswith("sha256:")

    findings = {
        finding["id"]: finding["correctiveWorkItem"] for finding in result["blockingFindings"]
    }
    assert findings == EXPECTED_FINDINGS


def test_japanese_corpus_preserves_authority_and_high_risk_stop_boundaries():
    by_id = {case["id"]: case for case in evaluate()["cases"]}

    assert by_id["JA-INPUT-001"]["status"] == "pass"
    assert by_id["JA-HIGH-RISK-001"]["status"] == "pass"
    assert by_id["JA-TASK-OUTCOME-001"]["status"] == "pass"
    assert by_id["JA-RELEASE-GATE-001"]["status"] == "pass"


def test_general_fluency_remains_a_limitation_not_a_pass():
    result = evaluate()
    by_id = {case["id"]: case for case in result["cases"]}

    assert by_id["JA-GENERAL-FLUENCY"]["status"] == "limitation"
    assert "human" in by_id["JA-GENERAL-FLUENCY"]["limitation"].lower()
    assert "general Japanese" in render_markdown(result)


def test_json_and_markdown_are_deterministic_views_of_one_result():
    first = evaluate()
    second = evaluate()

    assert first == second
    assert render_json(first) == render_json(second)
    markdown = render_markdown(first)
    assert first["digest"] in markdown
    assert "JA-CLI-001" in markdown
    status_case = next(case for case in first["cases"] if case["id"] == "JA-STATUS-001")
    assert status_case["status"] == "pass"
    assert "| `JA-STATUS-001` | Cockpit Status Japanese parity | **pass** |" in markdown
    assert "japanese-status-output-corrective-20260729" not in markdown


def test_report_drift_rejects_stale_json_and_markdown(tmp_path):
    result = evaluate()
    json_path = tmp_path / "assessment.json"
    markdown_path = tmp_path / "assessment.md"
    json_path.write_text(render_json(result), encoding="utf-8")
    markdown_path.write_text(render_markdown(result), encoding="utf-8")

    assert report_drift(result, json_path=json_path, markdown_path=markdown_path) == []

    json_path.write_text("{}\n", encoding="utf-8")
    assert report_drift(result, json_path=json_path, markdown_path=markdown_path) == [
        f"stale Japanese assessment JSON: {json_path}"
    ]
    json_path.write_text(render_json(result), encoding="utf-8")
    markdown_path.write_text("# stale\n", encoding="utf-8")
    assert report_drift(result, json_path=json_path, markdown_path=markdown_path) == [
        f"stale Japanese assessment Markdown: {markdown_path}"
    ]


def test_cli_writes_both_reports_and_returns_blocking(tmp_path, monkeypatch, capsys):
    json_path = tmp_path / "japanese-capability-assessment.json"
    markdown_path = tmp_path / "japanese-capability-assessment.md"
    monkeypatch.setattr(ai_japanese_capability, "JSON_REPORT_PATH", json_path)
    monkeypatch.setattr(ai_japanese_capability, "MARKDOWN_REPORT_PATH", markdown_path)
    monkeypatch.setattr(sys, "argv", ["ai_japanese_capability.py", "--write"])

    assert ai_japanese_capability.main() == 2
    assert json_path.is_file()
    assert markdown_path.is_file()
    assert "JA-STATUS-001" in markdown_path.read_text(encoding="utf-8")
    assert '"blockingFindings"' in capsys.readouterr().out


def test_cli_check_rejects_report_drift_before_reporting_blockers(tmp_path, monkeypatch, capsys):
    result = evaluate()
    json_path = tmp_path / "japanese-capability-assessment.json"
    markdown_path = tmp_path / "japanese-capability-assessment.md"
    json_path.write_text(render_json(result), encoding="utf-8")
    markdown_path.write_text("# stale\n", encoding="utf-8")
    monkeypatch.setattr(ai_japanese_capability, "JSON_REPORT_PATH", json_path)
    monkeypatch.setattr(ai_japanese_capability, "MARKDOWN_REPORT_PATH", markdown_path)
    monkeypatch.setattr(sys, "argv", ["ai_japanese_capability.py", "--check"])

    assert ai_japanese_capability.main() == 2
    assert "stale Japanese assessment Markdown" in capsys.readouterr().err
