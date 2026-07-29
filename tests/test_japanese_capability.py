import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
import ai_japanese_capability
from ai_japanese_capability import (
    CORPUS_PATH,
    evaluate,
    render_json,
    render_markdown,
    report_drift,
)


EXPECTED_FINDINGS = {}


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def test_evidence_source_identity_changes_when_bound_file_bytes_change(tmp_path):
    (tmp_path / "docs").mkdir()
    first = tmp_path / "docs/first.md"
    second = tmp_path / "docs/second.md"
    first.write_text("alpha\n", encoding="utf-8")
    second.write_text("beta\n", encoding="utf-8")

    before = ai_japanese_capability.build_evidence_source(
        ["docs/second.md", "docs/first.md"], root=tmp_path
    )
    first.write_text("alpha \n", encoding="utf-8")
    after = ai_japanese_capability.build_evidence_source(
        ["docs/second.md", "docs/first.md"], root=tmp_path
    )

    assert before["files"] == [
        {
            "path": "docs/first.md",
            "sha256": "b6a98d9ce9a2d9149288fa3df42d377c3e42737afdcdaf714e33c0a100b51060",
        },
        {
            "path": "docs/second.md",
            "sha256": "f2c82decdd7181cf98945929a62598db7e6b477e11f6e0eb0ae97020eff151ad",
        },
    ]
    assert after["files"][0] == {
        "path": "docs/first.md",
        "sha256": "94282539899bace79ab7110cb3e34b89cbe2bc965c3a9023d229baec25a555ea",
    }
    assert before["digest"] != after["digest"]


def test_evidence_source_normalizes_aliases_before_deduplicating(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/evidence.md").write_text("evidence\n", encoding="utf-8")

    result = ai_japanese_capability.build_evidence_source(
        ["docs/evidence.md", "docs/./evidence.md"],
        root=tmp_path,
    )

    assert result["fileCount"] == 1
    assert [entry["path"] for entry in result["files"]] == ["docs/evidence.md"]


def test_evidence_source_rejects_symbolic_links(tmp_path):
    target = tmp_path / "target.md"
    target.write_text("target\n", encoding="utf-8")
    (tmp_path / "alias.md").symlink_to(target)

    with pytest.raises(
        ai_japanese_capability.JapaneseCapabilityError,
        match="symbolic link",
    ):
        ai_japanese_capability.build_evidence_source(["alias.md"], root=tmp_path)


@pytest.mark.parametrize(
    ("relative", "setup", "diagnostic"),
    [
        ("missing.md", "missing", "missing"),
        ("directory", "directory", "regular file"),
        ("/absolute.md", "none", "repository-relative"),
        ("../escape.md", "none", "escapes repository"),
    ],
)
def test_evidence_source_identity_rejects_unbound_paths(tmp_path, relative, setup, diagnostic):
    if setup == "directory":
        (tmp_path / relative).mkdir()

    with pytest.raises(
        ai_japanese_capability.JapaneseCapabilityError,
        match=diagnostic,
    ):
        ai_japanese_capability.build_evidence_source([relative], root=tmp_path)


def test_assessment_inventory_binds_stable_evidence_not_transient_status():
    result = evaluate()
    paths = {entry["path"] for entry in result["evidenceSource"]["files"]}
    case_paths = {
        path
        for case in result["cases"]
        for field in ("sourceEvidence", "testEvidence")
        for path in case[field]
    }

    assert "scripts/ai_japanese_capability.py" in paths
    assert ".ai/cockpit/current_status.md" not in case_paths
    assert ".ai/cockpit/current_status.md" not in paths
    assert case_paths <= paths
    assert {
        "README.md",
        "README.zh-CN.md",
        "README.ja.md",
        "docs/trust-layer.md",
        "docs/trust-layer.zh-CN.md",
        "docs/trust-layer.ja.md",
        "docs/getting-started/security-release-verification.md",
        "docs/getting-started/security-release-verification.zh-CN.md",
        "docs/getting-started/security-release-verification.ja.md",
        "docs/reference/documentation-architecture.md",
        "docs/reference/documentation-architecture.ja.md",
        "docs/reference/capability-truth-matrix.json",
        "docs/reference/capability-truth-matrix.md",
    } <= paths


def test_expected_source_rejects_a_different_checked_out_head(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test User")
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("first\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-q", "-m", "first")
    first = _git(tmp_path, "rev-parse", "HEAD")
    tracked.write_text("second\n", encoding="utf-8")
    _git(tmp_path, "commit", "-q", "-am", "second")
    second = _git(tmp_path, "rev-parse", "HEAD")

    with pytest.raises(
        ai_japanese_capability.JapaneseCapabilityError,
        match=f"HEAD {second} does not match expected source {first}",
    ):
        ai_japanese_capability.validate_expected_source(tmp_path, first)


def test_expected_source_accepts_the_exact_checked_out_head(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "tracked.txt").write_text("only\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-q", "-m", "only")
    head = _git(tmp_path, "rev-parse", "HEAD")
    evidence_source = ai_japanese_capability.build_evidence_source(["tracked.txt"], root=tmp_path)

    assert (
        ai_japanese_capability.validate_expected_source(
            tmp_path, head, evidence_source=evidence_source
        )
        == head
    )


def test_expected_source_rejects_dirty_bound_evidence_at_the_same_head(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test User")
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("committed\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-q", "-m", "committed")
    head = _git(tmp_path, "rev-parse", "HEAD")
    tracked.write_text("dirty\n", encoding="utf-8")
    evidence_source = ai_japanese_capability.build_evidence_source(["tracked.txt"], root=tmp_path)

    with pytest.raises(
        ai_japanese_capability.JapaneseCapabilityError,
        match="tracked.txt bytes do not match expected source",
    ):
        ai_japanese_capability.validate_expected_source(
            tmp_path, head, evidence_source=evidence_source
        )


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


def test_pr_capability_requires_language_wiring_and_executable_safety_parity(tmp_path, monkeypatch):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts/ai_render_task_outcome_pr.py").write_text(
        'LANGUAGE_OPTION = "--language"\n日本語 = True\n',
        encoding="utf-8",
    )
    (tmp_path / "Makefile").write_text(
        'render-task-outcome-pr:\n\t--language "$(LANGUAGE)"\n',
        encoding="utf-8",
    )
    (tmp_path / "tests/test_task_outcome_pr_summary.py").write_text(
        "def test_japanese_pr_summary_localizes_chrome_and_preserves_approved_values(): pass\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_japanese_capability, "ROOT", tmp_path)

    assert ai_japanese_capability._pr_has_japanese_view() is False

    (tmp_path / "tests/test_task_outcome_pr_summary.py").write_text(
        "def test_japanese_pr_summary_localizes_chrome_and_preserves_approved_values(): pass\n"
        "def test_japanese_pr_summary_preserves_sanitization_and_opt_in_boundaries(): pass\n"
        "def test_cli_language_selection_and_unsupported_locale_fail_before_write(): pass\n",
        encoding="utf-8",
    )
    assert ai_japanese_capability._pr_has_japanese_view() is True


def test_lifecycle_capability_requires_named_install_calibration_recovery_and_removal_tests(
    tmp_path, monkeypatch
):
    tests = tmp_path / "tests"
    tests.mkdir()
    fixture = tests / "test_japanese_adopter_lifecycle.py"
    fixture.write_text(
        "def test_japanese_adopter_installs_with_real_wizard_and_release_binding(): pass\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_japanese_capability, "ROOT", tmp_path)

    assert ai_japanese_capability._lifecycle_fixture_exists() is False

    fixture.write_text(
        "def run_wizard(): pass\n"
        "def plan_rollback(): pass\n"
        "def execute_rollback(): pass\n"
        "def build_proposal(): pass\n"
        "def prepare_detached_removal(): pass\n"
        'ENTRYPOINT = "cockpit-calibrate-session"\n'
        "def test_japanese_adopter_installs_with_real_wizard_and_release_binding(): pass\n"
        "def test_japanese_adopter_calibration_pauses_and_resumes(): pass\n"
        "def test_japanese_adopter_recovery_is_confirmation_gated_and_preserves_project(): pass\n"
        "def test_japanese_adopter_removal_blocks_unknown_ownership_and_preserves_evidence(): pass\n",
        encoding="utf-8",
    )

    assert ai_japanese_capability._lifecycle_fixture_exists() is True


def test_uninstall_capability_rejects_keyword_only_and_requires_complete_actionable_path(
    tmp_path, monkeypatch
):
    installation = tmp_path / "docs/getting-started/installation.ja.md"
    installation.parent.mkdir(parents=True)
    installation.write_text("# アンインストール\n", encoding="utf-8")
    monkeypatch.setattr(ai_japanese_capability, "ROOT", tmp_path)

    assert ai_japanese_capability._uninstall_path_exists() is False

    installation.write_text(
        "# アンインストール\n"
        + "\n".join(ai_japanese_capability.JAPANESE_UNINSTALL_MARKERS)
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "docs/reference").mkdir()
    route = "installation.ja.md#15-ai-cockpit-を無効化またはアンインストールする"
    (tmp_path / "docs/reference/upgrade.ja.md").write_text(route, encoding="utf-8")
    (tmp_path / "docs/reference/troubleshooting.ja.md").write_text(route, encoding="utf-8")

    assert ai_japanese_capability._uninstall_path_exists() is True


def test_uninstall_capability_rejects_each_missing_actionable_step(tmp_path, monkeypatch):
    installation = tmp_path / "docs/getting-started/installation.ja.md"
    installation.parent.mkdir(parents=True)
    complete = "# アンインストール\n" + "\n".join(ai_japanese_capability.JAPANESE_UNINSTALL_MARKERS)
    (tmp_path / "docs/reference").mkdir()
    route = "installation.ja.md#15-ai-cockpit-を無効化またはアンインストールする"
    (tmp_path / "docs/reference/upgrade.ja.md").write_text(route, encoding="utf-8")
    (tmp_path / "docs/reference/troubleshooting.ja.md").write_text(route, encoding="utf-8")
    monkeypatch.setattr(ai_japanese_capability, "ROOT", tmp_path)

    for marker in ai_japanese_capability.JAPANESE_UNINSTALL_MARKERS:
        installation.write_text(complete.replace(marker, "", 1), encoding="utf-8")
        assert ai_japanese_capability._uninstall_path_exists() is False, marker


def test_uninstall_capability_rejects_out_of_order_actionable_steps(tmp_path, monkeypatch):
    installation = tmp_path / "docs/getting-started/installation.ja.md"
    installation.parent.mkdir(parents=True)
    installation.write_text(
        "# アンインストール\n"
        + "\n".join(reversed(ai_japanese_capability.JAPANESE_UNINSTALL_MARKERS)),
        encoding="utf-8",
    )
    (tmp_path / "docs/reference").mkdir()
    route = "installation.ja.md#15-ai-cockpit-を無効化またはアンインストールする"
    (tmp_path / "docs/reference/upgrade.ja.md").write_text(route, encoding="utf-8")
    (tmp_path / "docs/reference/troubleshooting.ja.md").write_text(route, encoding="utf-8")
    monkeypatch.setattr(ai_japanese_capability, "ROOT", tmp_path)

    assert ai_japanese_capability._uninstall_path_exists() is False


def test_uninstall_runtime_requires_a_public_installed_executor(tmp_path, monkeypatch):
    (tmp_path / "templates/make").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "templates/make/Makefile.ai").write_text(
        "ai-cockpit-uninstall-propose:\n", encoding="utf-8"
    )
    (tmp_path / "scripts/ai_detached_uninstaller.py").write_text(
        'def prepare():\n    return {"runtimeRemovalVerified": True}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_japanese_capability, "ROOT", tmp_path)

    assert ai_japanese_capability._public_uninstall_executor_exists() is False


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

    assert result["assessmentVersion"] == 3
    assert result["workItemId"] == "japanese-final-reassessment-after-documentation-truth-20260729"
    assert result["workItemRole"] == "final_reassessment"
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


def test_japanese_installation_session_evidence_boundary_is_current():
    result = evaluate()
    by_id = {case["id"]: case for case in result["cases"]}
    findings = {finding["id"] for finding in result["blockingFindings"]}

    assert by_id["JA-DOC-001"]["status"] == "pass"
    assert "JA-DOC-FACT-002" not in findings


def test_japanese_installation_session_evidence_boundary_fails_closed(tmp_path, monkeypatch):
    installation = tmp_path / "docs/getting-started/installation.ja.md"
    installation.parent.mkdir(parents=True)
    complete = (
        "<!-- calibration-session-evidence-boundary: "
        "combined-stage-seven-column-record,labels-not-actor-proof -->\n"
        "`checklistEvidence`\n"
        "本人確認\n"
        "役割分離\n"
    )
    installation.write_text(complete, encoding="utf-8")
    monkeypatch.setattr(ai_japanese_capability, "ROOT", tmp_path)

    assert ai_japanese_capability._calibration_session_evidence_boundary_is_truthful()
    for required in (
        "combined-stage-seven-column-record,labels-not-actor-proof",
        "checklistEvidence",
        "本人確認",
        "役割分離",
    ):
        installation.write_text(complete.replace(required, ""), encoding="utf-8")
        assert (
            ai_japanese_capability._calibration_session_evidence_boundary_is_truthful() is False
        ), required
        installation.write_text(complete, encoding="utf-8")


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
    assert (
        "- Assessment Work Item: "
        "`japanese-final-reassessment-after-documentation-truth-20260729`" in markdown
    )
    assert "- Work Item role: `final_reassessment`" in markdown
    assert "[Machine-readable assessment](japanese-capability-assessment.json)" in markdown
    assert "Assessment definition Work Item" not in markdown
    assert "JA-CLI-001" in markdown
    status_case = next(case for case in first["cases"] if case["id"] == "JA-STATUS-001")
    pr_case = next(case for case in first["cases"] if case["id"] == "JA-PR-001")
    assert status_case["status"] == "pass"
    assert pr_case["status"] == "pass"
    assert "| `JA-STATUS-001` | Cockpit Status Japanese parity | **pass** |" in markdown
    assert "japanese-status-output-corrective-20260729" not in markdown
    assert "japanese-pr-output-corrective-20260729" not in markdown


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


def test_bound_evidence_byte_drift_stales_both_reports_without_unrelated_false_positive(
    tmp_path,
):
    bound = tmp_path / "bound.md"
    unrelated = tmp_path / "unrelated.md"
    bound.write_text("bound\n", encoding="utf-8")
    unrelated.write_text("unrelated\n", encoding="utf-8")
    result = copy.deepcopy(evaluate())
    result["evidenceSource"] = ai_japanese_capability.build_evidence_source(
        ["bound.md"], root=tmp_path
    )
    result.pop("digest", None)
    result["digest"] = ai_japanese_capability._digest(result)
    json_path = tmp_path / "assessment.json"
    markdown_path = tmp_path / "assessment.md"
    json_path.write_text(render_json(result), encoding="utf-8")
    markdown_path.write_text(render_markdown(result), encoding="utf-8")

    unrelated.write_text("unrelated changed\n", encoding="utf-8")
    unchanged = copy.deepcopy(result)
    unchanged["evidenceSource"] = ai_japanese_capability.build_evidence_source(
        ["bound.md"], root=tmp_path
    )
    unchanged.pop("digest", None)
    unchanged["digest"] = ai_japanese_capability._digest(unchanged)
    assert report_drift(unchanged, json_path=json_path, markdown_path=markdown_path) == []

    bound.write_text("bound changed\n", encoding="utf-8")
    changed = copy.deepcopy(result)
    changed["evidenceSource"] = ai_japanese_capability.build_evidence_source(
        ["bound.md"], root=tmp_path
    )
    changed.pop("digest", None)
    changed["digest"] = ai_japanese_capability._digest(changed)
    assert report_drift(changed, json_path=json_path, markdown_path=markdown_path) == [
        f"stale Japanese assessment JSON: {json_path}",
        f"stale Japanese assessment Markdown: {markdown_path}",
    ]


def test_cli_rejects_an_explicit_empty_source_commit(monkeypatch, capsys):
    monkeypatch.setattr(
        sys, "argv", ["ai_japanese_capability.py", "--check", "--source-commit", ""]
    )

    assert ai_japanese_capability.main() == 2
    assert "source commit must not be empty" in capsys.readouterr().err


def test_cli_writes_both_reports_without_blocking_after_installed_lifecycle(
    tmp_path, monkeypatch, capsys
):
    json_path = tmp_path / "japanese-capability-assessment.json"
    markdown_path = tmp_path / "japanese-capability-assessment.md"
    monkeypatch.setattr(ai_japanese_capability, "JSON_REPORT_PATH", json_path)
    monkeypatch.setattr(ai_japanese_capability, "MARKDOWN_REPORT_PATH", markdown_path)
    monkeypatch.setattr(sys, "argv", ["ai_japanese_capability.py", "--write"])

    assert ai_japanese_capability.main() == 0
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


def test_release_requirement_accepts_fresh_final_reassessment(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai_japanese_capability.py", "--check", "--require-final-reassessment"],
    )

    assert ai_japanese_capability.main() == 0
    assert "requires workItemRole=final_reassessment" not in capsys.readouterr().err
