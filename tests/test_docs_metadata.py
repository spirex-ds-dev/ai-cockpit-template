import json
import shutil
import subprocess
from pathlib import Path

from check_docs_metadata import (
    beginner_installation_errors,
    check_repository,
    command_evidence_errors,
    documentation_fact_errors,
    historical_context_errors,
    japanese_uninstall_errors,
    multilingual_layer_errors,
)


ROOT = Path(__file__).resolve().parents[1]


def copy_documentation(target: Path) -> None:
    for name in ("README.md", "README.ja.md", "README.zh-CN.md"):
        shutil.copy2(ROOT / name, target / name)
    shutil.copytree(ROOT / "docs", target / "docs")
    shutil.copytree(ROOT / "examples", target / "examples")
    (target / ".ai").mkdir()
    shutil.copy2(ROOT / ".ai" / "README.md", target / ".ai" / "README.md")
    shutil.copy2(ROOT / ".ai" / "glossary.md", target / ".ai" / "glossary.md")
    shutil.copy2(ROOT / "release.json", target / "release.json")
    shutil.copy2(ROOT / "install.sh", target / "install.sh")
    shutil.copy2(ROOT / "Makefile", target / "Makefile")


def test_repository_documentation_metadata_is_consistent():
    assert check_repository(ROOT) == []


def test_wi10_layered_documents_are_complete_and_trilingual():
    assert multilingual_layer_errors(ROOT) == []


def test_wi10_authoritative_command_examples_have_evidence_labels():
    assert command_evidence_errors(ROOT) == []


def test_wi10_beginner_installation_routes_are_complete():
    assert beginner_installation_errors(ROOT) == []


def test_wi10_beginner_check_rejects_missing_installation_proofreading_checklist(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.ja.md"
    installation.write_text(
        installation.read_text(encoding="utf-8").replace(
            "<!-- installation-proofreading-checklist: "
            "version-neutral,prompt-first,steps,calibration,platforms,tables,links,lifecycle -->\n",
            "",
            1,
        ),
        encoding="utf-8",
    )

    assert (
        "docs/getting-started/installation.ja.md: missing installation proofreading decision table"
        in beginner_installation_errors(tmp_path)
    )


def test_wi10_beginner_check_rejects_hidden_version_neutral_or_proofreading_copy(tmp_path):
    copy_documentation(tmp_path)
    english = tmp_path / "docs/getting-started/installation.md"
    english.write_text(
        english.read_text(encoding="utf-8").replace(
            "This guide is version-neutral:",
            "This guide selects a release:",
            1,
        ),
        encoding="utf-8",
    )
    chinese = tmp_path / "docs/getting-started/installation.zh-CN.md"
    chinese.write_text(
        chinese.read_text(encoding="utf-8").replace(
            "## 安装文档校对清单",
            "## 安装文档",
            1,
        ),
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/installation.md: missing reader-visible version-neutral rule"
        in errors
    )
    assert (
        "docs/getting-started/installation.zh-CN.md: missing reader-visible "
        "installation proofreading heading"
    ) in errors


def test_wi10_beginner_check_rejects_interrupted_or_malformed_proofreading_table(tmp_path):
    copy_documentation(tmp_path)
    english = tmp_path / "docs/getting-started/installation.md"
    english.write_text(
        english.read_text(encoding="utf-8").replace(
            "| 4 | Calibration coverage",
            "<!-- split-proofreading-table -->\n| 4 | Calibration coverage",
            1,
        ),
        encoding="utf-8",
    )
    japanese = tmp_path / "docs/getting-started/installation.ja.md"
    japanese.write_text(
        japanese.read_text(encoding="utf-8").replace(
            "| 6 | 表の表示 |",
            "| 6 | 表の表示 | 余分な列 |",
            1,
        ),
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/installation.md: installation proofreading table "
        "must be one uninterrupted Markdown table"
    ) in errors
    assert (
        "docs/getting-started/installation.ja.md: installation proofreading row 6 "
        "must contain 5 columns"
    ) in errors


def test_wi10_beginner_check_rejects_missing_chinese_installation(tmp_path):
    copy_documentation(tmp_path)
    chinese = tmp_path / "docs/getting-started/installation.zh-CN.md"
    if chinese.exists():
        chinese.unlink()

    assert (
        "docs/getting-started/installation.zh-CN.md: required beginner installation guide is missing"
        in beginner_installation_errors(tmp_path)
    )


def test_wi10_beginner_check_rejects_missing_novice_or_calibration_stage(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.md"
    text = installation.read_text(encoding="utf-8")
    text = text.replace("<!-- novice-stage: inspect-scaffold -->", "", 1)
    text = text.replace("<!-- calibration-stage: critical-paths -->", "", 1)
    installation.write_text(text, encoding="utf-8")

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/installation.md: missing novice installation stage: inspect-scaffold"
        in errors
    )
    assert (
        "docs/getting-started/installation.md: missing calibration stage: critical-paths" in errors
    )


def test_wi10_beginner_check_rejects_missing_prompt_boundary_or_command_explanation(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.ja.md"
    text = installation.read_text(encoding="utf-8")
    text = text.replace("<!-- prompt-safety: read-only-discovery -->", "", 1)
    text = text.replace("<!-- command-guide: purpose,success,failure -->", "", 1)
    installation.write_text(text, encoding="utf-8")

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/installation.ja.md: missing prompt safety boundary: "
        "read-only-discovery"
    ) in errors
    assert (
        "docs/getting-started/installation.ja.md: retained commands require purpose, success, "
        "and failure guidance"
    ) in errors


def test_japanese_uninstall_check_rejects_keyword_only_or_missing_actionable_step(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.ja.md"
    installation.write_text(
        "# アンインストール\nアンインストールできます。\n",
        encoding="utf-8",
    )

    errors = japanese_uninstall_errors(tmp_path)
    assert any("missing actionable uninstall step" in error for error in errors)


def test_japanese_uninstall_check_accepts_repository_procedure():
    assert japanese_uninstall_errors(ROOT) == []


def test_wi10_beginner_check_rejects_moving_or_hardcoded_release_metadata(tmp_path):
    copy_documentation(tmp_path)
    chinese = tmp_path / "docs/getting-started/installation.zh-CN.md"
    chinese.write_text(
        chinese.read_text(encoding="utf-8").replace(
            "<resolved-tag>/release.json",
            "main/release.json",
            1,
        ),
        encoding="utf-8",
    )
    english = tmp_path / "docs/getting-started/installation.md"
    english.write_text(
        english.read_text(encoding="utf-8").replace(
            "<resolved-tag>/release.json",
            "v9.9.9/release.json",
            1,
        ),
        encoding="utf-8",
    )
    japanese = tmp_path / "docs/getting-started/installation.ja.md"
    japanese.write_text(
        japanese.read_text(encoding="utf-8").replace(
            "<!-- release-metadata-boundary: "
            "provider-discovers-latest-verifiable,tag-pinned-verifies-evidence -->",
            "",
            1,
        ),
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/installation.zh-CN.md: moving main release metadata "
        "must not verify a tagged asset"
    ) in errors
    assert (
        "docs/getting-started/installation.md: installation discovery must not "
        "hardcode a release version"
    ) in errors
    assert (
        "docs/getting-started/installation.ja.md: missing dynamic tag-pinned "
        "release metadata boundary"
    ) in errors


def test_wi10_beginner_check_rejects_missing_answer_mapping_or_activation_stage(tmp_path):
    copy_documentation(tmp_path)
    japanese = tmp_path / "docs/getting-started/installation.ja.md"
    japanese.write_text(
        japanese.read_text(encoding="utf-8")
        .replace(
            "<!-- calibration-answer-types: yes_no,alternative_input,unknown,not_applicable -->",
            "",
            1,
        )
        .replace("<!-- calibration-activation: bounded-approval -->", "", 1),
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/installation.ja.md: missing exact Calibration Session "
        "answer-type mapping"
    ) in errors
    assert (
        "docs/getting-started/installation.ja.md: missing separate calibration "
        "activation stage: bounded-approval"
    ) in errors


def test_wi10_beginner_check_requires_runtime_boundary_and_release_bound_plan(tmp_path):
    copy_documentation(tmp_path)
    english = tmp_path / "docs/getting-started/installation.md"
    english.write_text(
        english.read_text(encoding="utf-8")
        .replace(
            "<!-- calibration-runtime-boundary: "
            "unknown-machine-blocked,confirmations-candidate-bound -->",
            "",
            1,
        )
        .replace(
            "<!-- installation-plan-release-binding: "
            "resolved-tag,metadata,asset,digest,installer,wizard -->",
            "",
            1,
        ),
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)

    assert (
        "docs/getting-started/installation.md: missing current Calibration Session runtime boundary"
    ) in errors
    assert (
        "docs/getting-started/installation.md: installation plan must bind verified "
        "release evidence to the installer entrypoint"
    ) in errors


def test_wi10_beginner_check_rejects_obsolete_calibration_runtime_boundary(tmp_path):
    copy_documentation(tmp_path)
    english = tmp_path / "docs/getting-started/installation.md"
    english.write_text(
        english.read_text(encoding="utf-8") + "\n<!-- calibration-runtime-boundary: "
        "unknown-not-machine-blocked,confirmations-not-candidate-bound -->\n",
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)

    assert (
        "docs/getting-started/installation.md: obsolete non-enforced Calibration "
        "runtime boundary must be removed"
    ) in errors


def test_wi10_beginner_check_requires_release_make_confirmation_and_ci_boundaries(tmp_path):
    copy_documentation(tmp_path)
    chinese = tmp_path / "docs/getting-started/installation.zh-CN.md"
    text = chinese.read_text(encoding="utf-8")
    for marker in (
        "<!-- release-fallback-approval: failed-newer-evidence,owner-review,reverify -->",
        "<!-- make-entrypoint-boundary: included-makefile-or-explicit-f -->",
        "<!-- calibration-yes-no: type=yes_no,values=Y-or-N -->",
        "<!-- calibration-confirmation-boundary: phase-records,external-actor-identity -->",
        "<!-- calibration-ci-gap-boundary: plan,approval,implementation,verification -->",
        "<!-- calibration-session-persistence-boundary: "
        "structured-checklist-evidence,candidate-bound -->",
        "<!-- calibration-activation-atomicity: "
        "active-session-rollback-transaction,candidate-digest-bound -->",
        "<!-- make-composite-boundary: selected-entrypoint-propagates-through-ai-finish -->",
    ):
        text = text.replace(marker, "", 1)
    chinese.write_text(text, encoding="utf-8")

    errors = beginner_installation_errors(tmp_path)

    assert (
        "docs/getting-started/installation.zh-CN.md: missing bounded older-release "
        "fallback approval"
    ) in errors
    assert (
        "docs/getting-started/installation.zh-CN.md: missing installed Make entrypoint boundary"
    ) in errors
    assert (
        "docs/getting-started/installation.zh-CN.md: missing yes_no type and Y/N value boundary"
    ) in errors
    assert (
        "docs/getting-started/installation.zh-CN.md: missing confirmation phase and "
        "actor-identity boundary"
    ) in errors
    assert (
        "docs/getting-started/installation.zh-CN.md: missing CI-gap plan, approval, "
        "implementation, and verification path"
    ) in errors
    assert (
        "docs/getting-started/installation.zh-CN.md: missing Session checklist-persistence boundary"
    ) in errors
    assert (
        "docs/getting-started/installation.zh-CN.md: missing Active/Session atomicity boundary"
    ) in errors
    assert (
        "docs/getting-started/installation.zh-CN.md: missing composite Make entrypoint "
        "propagation boundary"
    ) in errors


def test_wi10_beginner_check_requires_transaction_runtime_terms(tmp_path):
    copy_documentation(tmp_path)
    japanese = tmp_path / "docs/getting-started/installation.ja.md"
    text = japanese.read_text(encoding="utf-8")
    for runtime_term in ("`record-evidence`", "`prepare-candidate`", "consistency unproved"):
        text = text.replace(runtime_term, "", 1)
    japanese.write_text(text, encoding="utf-8")

    errors = beginner_installation_errors(tmp_path)

    for runtime_term in ("`record-evidence`", "`prepare-candidate`", "consistency unproved"):
        assert (
            "docs/getting-started/installation.ja.md: missing Calibration transaction "
            f"runtime term: {runtime_term}"
        ) in errors


def test_wi10_beginner_check_rejects_missing_platform_language_or_stage(tmp_path):
    copy_documentation(tmp_path)
    android = tmp_path / "docs/getting-started/examples/android.zh-CN.md"
    if android.exists():
        android.unlink()
    ios = tmp_path / "docs/getting-started/examples/ios.md"
    if ios.exists():
        ios.write_text(
            ios.read_text(encoding="utf-8").replace(
                "<!-- platform-stage: discover-quality-commands -->", "", 1
            ),
            encoding="utf-8",
        )

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/examples/android.zh-CN.md: required platform installation "
        "example is missing"
    ) in errors
    assert (
        "docs/getting-started/examples/ios.md: missing platform installation stage: "
        "discover-quality-commands"
    ) in errors


def test_wi10_beginner_check_rejects_platform_overclaim_boundary_or_same_language_link(
    tmp_path,
):
    copy_documentation(tmp_path)
    java = tmp_path / "docs/getting-started/examples/java.ja.md"
    if java.exists():
        java.write_text(
            java.read_text(encoding="utf-8").replace(
                "<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->", "", 1
            ),
            encoding="utf-8",
        )
    readme = tmp_path / "README.zh-CN.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "docs/getting-started/installation.zh-CN.md", "docs/getting-started/installation.md"
        ),
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/examples/java.ja.md: missing platform evidence boundary"
    ) in errors
    assert (
        "README.zh-CN.md: missing same-language beginner installation entry: "
        "docs/getting-started/installation.zh-CN.md"
    ) in errors


def test_wi10_beginner_check_rejects_unsafe_prompt_or_lifecycle_order_loss(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.md"
    installation.write_text(
        installation.read_text(encoding="utf-8")
        .replace(
            "Do not create, edit, delete, commit, push, open or merge a PR, or publish.",
            "Commit and push all installation changes.",
            1,
        )
        .replace("<!-- lifecycle-order: adoption-close-before-configuration -->", "", 1),
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)
    assert any("lost its no-write/no-downstream-authority sentence" in error for error in errors)
    assert any("adoption must close before configuration starts" in error for error in errors)


def test_wi10_beginner_check_rejects_platform_without_copy_ready_prompt(tmp_path):
    copy_documentation(tmp_path)
    android = tmp_path / "docs/getting-started/examples/android.ja.md"
    android.write_text(
        android.read_text(encoding="utf-8").replace("<!-- platform-prompt: copy-ready -->", "", 1),
        encoding="utf-8",
    )

    assert (
        "docs/getting-started/examples/android.ja.md: missing copy-ready platform prompt"
        in beginner_installation_errors(tmp_path)
    )


def test_wi10_beginner_check_rejects_incomplete_decision_tables(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.zh-CN.md"
    installation.write_text(
        installation.read_text(encoding="utf-8").replace(
            "| 7. 可选 examples | “说明是否请求 examples、全部路径，以及为何它们不能证明本工程 stack。” | 没有 examples，或只有计划批准的路径。 | 选择与计划一致。 | 未请求文件或能力夸大；只能在修订计划获批后移除。 |\n",
            "",
            1,
        ),
        encoding="utf-8",
    )
    ios = tmp_path / "docs/getting-started/examples/ios.ja.md"
    ios.write_text(
        ios.read_text(encoding="utf-8").replace(
            "「repo/CI 出典どおりの正確な command と scheme、destination、"
            "configuration、前提、成功/失敗を説明し、創作しないでください。」",
            "copy request missing",
            1,
        ),
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/installation.zh-CN.md: scaffold review decision table must "
        "contain 7 rows"
    ) in errors
    assert (
        "docs/getting-started/examples/ios.ja.md: platform step row 4 lacks a copy-ready request"
    ) in errors


def test_wi10_beginner_check_rejects_merged_calibration_request_and_example(tmp_path):
    copy_documentation(tmp_path)
    japanese = tmp_path / "docs/getting-started/installation.ja.md"
    japanese.write_text(
        japanese.read_text(encoding="utf-8").replace(
            "まだ回答を記録しません。」 | release workflow",
            "まだ回答を記録しません。」release workflow",
            1,
        ),
        encoding="utf-8",
    )

    assert (
        "docs/getting-started/installation.ja.md: calibration review row 1 must contain 5 columns"
    ) in beginner_installation_errors(tmp_path)


def test_wi10_beginner_check_rejects_interrupted_platform_table(tmp_path):
    copy_documentation(tmp_path)
    ios = tmp_path / "docs/getting-started/examples/ios.md"
    text = ios.read_text(encoding="utf-8")
    text = text.replace("<!-- platform-stage5: proposal-only -->\n", "", 1)
    text = text.replace(
        "| 4 Commands |",
        "<!-- platform-stage5: proposal-only -->\n| 4 Commands |",
        1,
    )
    text = text.replace(
        "| 3 Boundaries |",
        "| 3 Boundaries |",
        1,
    ).replace(
        "\n| 4 Commands |",
        "\n<!-- interruption-that-breaks-github-table -->\n| 4 Commands |",
        1,
    )
    ios.write_text(text, encoding="utf-8")

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/examples/ios.md: platform step table must be one "
        "uninterrupted Markdown table"
    ) in errors


def test_wi10_beginner_check_requires_seven_stage_filled_examples(tmp_path):
    copy_documentation(tmp_path)
    ios = tmp_path / "docs/getting-started/examples/ios.md"
    ios.write_text(
        ios.read_text(encoding="utf-8").replace(
            "<!-- platform-filled-example: seven-stages -->", "", 1
        ),
        encoding="utf-8",
    )
    japanese = tmp_path / "docs/getting-started/examples/android.ja.md"
    marker = "<!-- platform-filled-example: seven-stages -->"
    before, separator, after = japanese.read_text(encoding="utf-8").partition(marker)
    japanese.write_text(
        before + separator + after.replace("\n| 4 |", "\n\n| 4 |", 1),
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)

    assert (
        "docs/getting-started/examples/ios.md: missing platform filled example decision table"
    ) in errors
    assert (
        "docs/getting-started/examples/android.ja.md: platform filled example table "
        "must be one uninterrupted Markdown table"
    ) in errors


def test_wi10_beginner_check_rejects_platform_table_blank_or_misplaced_marker(tmp_path):
    copy_documentation(tmp_path)
    android = tmp_path / "docs/getting-started/examples/android.zh-CN.md"
    text = android.read_text(encoding="utf-8")
    text = text.replace("<!-- platform-stage5: proposal-only -->\n", "", 1)
    text = text.replace(
        "\n| 5 校准 |",
        "\n\n| 5 校准 |",
        1,
    )
    text = text.replace(
        "\n| 7 验证 |",
        "\n<!-- platform-stage5: proposal-only -->\n| 7 验证 |",
        1,
    )
    android.write_text(text, encoding="utf-8")

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/examples/android.zh-CN.md: platform step table must be one "
        "uninterrupted Markdown table"
    ) in errors
    assert (
        "docs/getting-started/examples/android.zh-CN.md: platform Stage 5 proposal-only "
        "marker must remain outside the table"
    ) in errors


def test_wi10_beginner_check_rejects_missing_complete_calibration_checklist(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.zh-CN.md"
    installation.write_text(
        installation.read_text(encoding="utf-8").replace(
            "<!-- calibration-completion-checklist: "
            "state,evidence,answer,candidate,owner-reviewer,pass-stop -->\n",
            "",
            1,
        ),
        encoding="utf-8",
    )

    assert (
        "docs/getting-started/installation.zh-CN.md: missing complete calibration checklist"
        in beginner_installation_errors(tmp_path)
    )


def test_wi10_beginner_check_rejects_incomplete_calibration_checklist_field(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.md"
    installation.write_text(
        installation.read_text(encoding="utf-8").replace(
            "Record Candidate role fields or `no change` with reason: ___",
            "Record proposed role fields: ___",
            1,
        ),
        encoding="utf-8",
    )

    assert (
        "docs/getting-started/installation.md: calibration checklist row 1 lacks Candidate change"
    ) in beginner_installation_errors(tmp_path)


def test_wi10_beginner_check_rejects_calibration_checklist_language_drift(tmp_path):
    copy_documentation(tmp_path)
    japanese = tmp_path / "docs/getting-started/installation.ja.md"
    japanese.write_text(
        japanese.read_text(encoding="utf-8").replace(
            "1. repository-role",
            "1. repository-kind",
            1,
        ),
        encoding="utf-8",
    )

    assert (
        "docs/getting-started/installation.ja.md: calibration checklist stage IDs "
        "must match the ten-stage calibration order"
    ) in beginner_installation_errors(tmp_path)


def test_wi10_beginner_check_rejects_crossed_commit_or_candidate_authority(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "make ai-finish TASK=adopt_ai_cockpit\n```\n\nStop and review the archive/diff. "
            "After separate human commit approval:\n\n"
            "<!-- command-evidence: adopter_required -->\n```sh\n",
            "make ai-finish TASK=adopt_ai_cockpit\n",
            1,
        ),
        encoding="utf-8",
    )
    java = tmp_path / "docs/getting-started/examples/java.zh-CN.md"
    java.write_text(
        java.read_text(encoding="utf-8").replace("<!-- platform-stage5: proposal-only -->", "", 1),
        encoding="utf-8",
    )
    installation = tmp_path / "docs/getting-started/installation.ja.md"
    installation.write_text(
        installation.read_text(encoding="utf-8").replace(
            "<!-- lifecycle-approval: configuration-closure-execute -->", "", 1
        ),
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)
    assert "README.md: finish and commit must use separate command blocks" in errors
    assert (
        "docs/getting-started/examples/java.zh-CN.md: platform Stage 5 must remain proposal-only"
        in errors
    )
    assert (
        "docs/getting-started/installation.ja.md: missing separate lifecycle approval: "
        "configuration-closure-execute"
    ) in errors


def test_historical_context_registry_is_complete_and_non_authoritative():
    assert historical_context_errors(ROOT) == []


def test_wi10_check_rejects_missing_language_layer(tmp_path):
    copy_documentation(tmp_path)
    (tmp_path / "docs/getting-started/30-second-start.ja.md").unlink()

    errors = multilingual_layer_errors(tmp_path)
    assert (
        "docs/getting-started/30-second-start.ja.md: required WI-10 language document is missing"
    ) in errors


def test_wi10_check_rejects_unlabeled_authoritative_command(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.md"
    installation.write_text(
        installation.read_text(encoding="utf-8").replace(
            "<!-- command-evidence: adopter_required -->\n```sh",
            "```sh",
            1,
        ),
        encoding="utf-8",
    )

    assert any(
        "executable command fence is missing command-evidence" in error
        for error in command_evidence_errors(tmp_path)
    )


def test_wi10_check_rejects_unknown_or_duplicate_command_evidence(tmp_path):
    copy_documentation(tmp_path)
    start = tmp_path / "docs/getting-started/30-second-start.md"
    text = start.read_text(encoding="utf-8")
    text = text.replace(
        "<!-- command-evidence: adopter_required -->",
        "<!-- command-evidence: illustrative_only -->\n<!-- command-evidence: adopter_required -->",
        1,
    )
    start.write_text(text, encoding="utf-8")
    chinese = tmp_path / "docs/getting-started/30-second-start.zh-CN.md"
    chinese.write_text(
        chinese.read_text(encoding="utf-8").replace(
            "<!-- command-evidence: adopter_required -->",
            "<!-- command-evidence: unsupported_claim -->",
            1,
        ),
        encoding="utf-8",
    )

    errors = command_evidence_errors(tmp_path)
    assert any("unknown command evidence label: unsupported_claim" in error for error in errors)
    assert any(
        "command-evidence is not attached to an executable fence" in error for error in errors
    )


def test_wi10_check_rejects_semantic_domain_or_capability_truth_drift(tmp_path):
    copy_documentation(tmp_path)
    adoption = tmp_path / "docs/getting-started/standard-adoption-guide.zh-CN.md"
    adoption.write_text(
        adoption.read_text(encoding="utf-8").replace("<!-- semantic-domain: north-star -->", "", 1),
        encoding="utf-8",
    )
    security = tmp_path / "docs/getting-started/security-release-verification.zh-CN.md"
    security.write_text(
        security.read_text(encoding="utf-8").replace(
            "../reference/capability-truth-matrix.md", "missing-capability-source"
        ),
        encoding="utf-8",
    )

    errors = multilingual_layer_errors(tmp_path)
    assert "README.zh-CN.md: missing semantic domain: north-star" in errors
    assert "README.zh-CN.md: layered guidance must link Capability Truth Matrix" in errors


def test_wi10_check_rejects_installer_option_or_environment_drift(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.md"
    installation.write_text(
        installation.read_text(encoding="utf-8")
        .replace("--upgrade-with-active", "--removed-active-upgrade")
        .replace("AI_COCKPIT_TEMPLATE_SHA256", "REMOVED_TEMPLATE_SHA256"),
        encoding="utf-8",
    )

    errors = check_repository(tmp_path)
    assert (
        "docs/getting-started/installation.md: "
        "implemented installer option is undocumented: --upgrade-with-active"
    ) in errors
    assert (
        "docs/getting-started/installation.md: "
        "installer environment variable is undocumented: AI_COCKPIT_TEMPLATE_SHA256"
    ) in errors


def test_wi10_check_rejects_coverage_base_or_lifecycle_fact_drift(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.ja.md"
    text = readme.read_text(encoding="utf-8")
    text = text.replace("85.10%", "80%", 1)
    contract_line = next(
        line for line in text.splitlines() if line.startswith('ADOPTION_CONTRACT="')
    )
    text = text.replace(contract_line, "", 1)
    text = text.replace(
        'STACK="${STACK:-generic}"',
        f'{contract_line}\nSTACK="${{STACK:-generic}}"',
        1,
    )
    readme.write_text(text, encoding="utf-8")

    adoption = tmp_path / "docs/getting-started/standard-adoption-guide.ja.md"
    adoption.write_text(
        adoption.read_text(encoding="utf-8").replace(
            'git commit -m "adopt AI Cockpit governance"\n', "", 1
        ),
        encoding="utf-8",
    )

    errors = documentation_fact_errors(tmp_path)
    assert "README.ja.md: documented coverage floor differs from Makefile: 85.10%" in errors
    assert (
        "README.ja.md: adoption PR check must reload archived Contract base after finish approval"
        in errors
    )
    assert any(
        "adoption lifecycle must commit archive evidence before PR check and closure" in error
        for error in errors
    )


def test_readme_adoption_base_snippet_works_after_active_contract_is_archived(tmp_path):
    archive = tmp_path / ".ai/work-items/archive/2026"
    archive.mkdir(parents=True)
    contract = archive / "adopt_ai_cockpit.contract.json"
    contract.write_text(json.dumps({"baseCommit": "a" * 40}), encoding="utf-8")
    index = tmp_path / ".ai/work-items/archive/index.json"
    index.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "workItemId": "adopt_ai_cockpit",
                        "contractPath": ".ai/work-items/archive/2026/adopt_ai_cockpit.contract.json",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    body = next(
        part
        for part in readme.split("```sh\n")
        if part.startswith('ADOPTION_CONTRACT="$(python3 -c')
    ).split("\n```", 1)[0]
    discovery = "\n".join(body.splitlines()[:2]) + '\nprintf "%s" "$ADOPTION_BASE"\n'

    result = subprocess.run(
        ["sh", "-c", discovery],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "a" * 40


def test_wi10_check_rejects_ui_localization_or_published_tag_overclaim(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + "\nJapanese is the default UI locale; use the highest published semantic-version tag.\n",
        encoding="utf-8",
    )

    errors = documentation_fact_errors(tmp_path)
    assert any("Japanese is the default UI locale" in error for error in errors)
    assert any("highest published semantic-version tag" in error for error in errors)


def test_wi10_check_rejects_historical_record_without_boundary_marker(tmp_path):
    copy_documentation(tmp_path)
    plan = tmp_path / "docs/superpowers/plans/2026-07-14-review-remediation-loop.md"
    plan.write_text(
        plan.read_text(encoding="utf-8").replace(
            "> **Historical Record**\n"
            "> **Not Current Product Documentation**\n"
            "> **Do Not Use As Runtime Instruction**\n",
            "",
            1,
        ),
        encoding="utf-8",
    )

    assert (
        "docs/superpowers/plans/2026-07-14-review-remediation-loop.md: "
        "missing historical context marker"
    ) in historical_context_errors(tmp_path)


def test_quick_install_examples_match_installer_contract():
    for name in ("README.md", "README.zh-CN.md", "README.ja.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert 'AI_COCKPIT_TEMPLATE_REPO="$PUBLIC_REPOSITORY"' in text
        assert "AI_COCKPIT_TEMPLATE_PUBLIC_REPOSITORY" in text
        assert "https://github.com/spirex-ds-dev/ai-cockpit-template.git" in text
        assert "https://raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template" in text
        if name != "README.md":
            assert "<owner>/<repo>" not in text

    installation = (ROOT / "docs" / "getting-started" / "installation.md").read_text(
        encoding="utf-8"
    )
    assert "Skipping status check (no active contract/summary provided)" in installation
    assert "check-ai-status-consistency" in installation

    upgrade = (ROOT / "docs" / "reference" / "upgrade.md").read_text(encoding="utf-8")
    assert "release semver" in upgrade


def test_check_rejects_supported_stack_drift(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8").replace(", android", ""), encoding="utf-8")

    assert "README.md: supported-stack list does not match installer STACKS" in check_repository(
        tmp_path
    )


def test_check_rejects_stack_tier_drift(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.zh-CN.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "verified=python,go,rust,typescript,java,kotlin,ruby,php,csharp,flutter,android,swift",
            "verified=python",
        ),
        encoding="utf-8",
    )

    assert (
        "README.zh-CN.md: stack compatibility tiers do not match executable CI evidence"
        in check_repository(tmp_path)
    )


def test_check_rejects_configuration_stack_tier_drift(tmp_path):
    copy_documentation(tmp_path)
    configuration = tmp_path / "docs" / "configuration.md"
    configuration.write_text(
        configuration.read_text(encoding="utf-8").replace(
            "preset-only=generic",
            "preset-only=generic,flutter",
        ),
        encoding="utf-8",
    )

    assert (
        "docs/configuration.md: stack compatibility tiers do not match executable CI evidence"
        in check_repository(tmp_path)
    )


def test_check_rejects_release_capability_drift(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.ja.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "<!-- release-capabilities: auditable-adoption,sha256-verification -->",
            "<!-- release-capabilities: runtime-only -->",
        ),
        encoding="utf-8",
    )

    assert "README.ja.md: release capability marker is missing or inconsistent" in check_repository(
        tmp_path
    )


def test_check_rejects_public_quality_target_drift(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.zh-CN.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "<!-- public-quality-target: ai-cockpit-quality -->",
            "<!-- public-quality-target: quality -->",
        ),
        encoding="utf-8",
    )

    assert "README.zh-CN.md: public quality target differs from release.json" in check_repository(
        tmp_path
    )


def test_check_rejects_public_quality_command_drift(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "CI wiring for both `ai-cockpit-quality` and `check-ai-pr`",
            "CI wiring for both `quality` and `check-ai-pr`",
        ),
        encoding="utf-8",
    )
    installation = tmp_path / "docs" / "getting-started" / "installation.md"
    installation.write_text(
        installation.read_text(encoding="utf-8").replace(
            "<!-- readiness-target-order: ai-cockpit-quality,check-ai-adoption-ready -->",
            "<!-- readiness-target-order: quality,check-ai-adoption-ready -->",
        ),
        encoding="utf-8",
    )

    errors = check_repository(tmp_path)
    assert "README.md: readiness guidance does not use the public quality target" in errors
    assert (
        "docs/getting-started/installation.md: readiness commands do not use the public quality target"
        in errors
    )


def test_check_accepts_prompt_first_readiness_target_order(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs" / "getting-started" / "installation.md"
    text = installation.read_text(encoding="utf-8")
    text = text.replace(
        "<!-- public-quality-target: ai-cockpit-quality -->",
        "<!-- public-quality-target: ai-cockpit-quality -->\n"
        "<!-- readiness-target-order: "
        "ai-cockpit-quality,check-ai-adoption-ready -->",
        1,
    )
    installation.write_text(text, encoding="utf-8")

    errors = check_repository(tmp_path)

    assert (
        "docs/getting-started/installation.md: readiness commands do not use the public quality target"
        not in errors
    )


def test_check_rejects_missing_front_matter_field(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.ja.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace("author: Ray\n", ""), encoding="utf-8"
    )

    assert any(
        error.endswith("README.ja.md: front matter missing author")
        for error in check_repository(tmp_path)
    )


def test_check_rejects_prerequisites_after_install_command(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.md"
    marker = "<!-- install-prerequisites: python3.10,git-initial-commit,curl,gnu-make,posix -->"
    text = readme.read_text(encoding="utf-8").replace(marker, "") + f"\n{marker}\n"
    readme.write_text(text, encoding="utf-8")

    assert (
        "README.md: installation prerequisites must precede the primary install command"
        in check_repository(tmp_path)
    )


def test_check_rejects_mutable_or_incomplete_install_commands(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + '\nsh -c "$(curl -fsSL https://raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template/main/install.sh)" -- --stack rust\n',
        encoding="utf-8",
    )

    errors = check_repository(tmp_path)
    assert any("remote installer must use a fixed tag or commit" in error for error in errors)
    assert any(
        "install command with --stack requires --update-makefile" in error for error in errors
    )


def test_check_rejects_install_commands_without_adoption_evidence(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.ja.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(" --create-adoption", "", 1), encoding="utf-8"
    )
    example = tmp_path / "examples" / "python" / "README.md"
    example.write_text(
        example.read_text(encoding="utf-8").replace(" --create-adoption", ""), encoding="utf-8"
    )

    errors = check_repository(tmp_path)
    assert "README.ja.md: primary install command must create auditable adoption evidence" in errors
    assert any(
        "example install command must create auditable adoption evidence" in error
        for error in errors
    )


def test_check_rejects_readme_that_calibrates_before_finishing_adoption(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = text.replace("make ai-finish TASK=adopt_ai_cockpit", "make ai-finish TASK=other")
    readme.write_text(text, encoding="utf-8")
    assert any("primary adoption flow must finish" in error for error in check_repository(tmp_path))


def test_check_rejects_language_specific_default_stack(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.ja.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        .replace('STACK="${STACK:-generic}"', 'STACK="${STACK:-rust}"')
        .replace('--stack "$STACK"', "--stack rust"),
        encoding="utf-8",
    )

    assert (
        "README.ja.md: primary install command must use an explicit generic-default STACK variable"
        in check_repository(tmp_path)
    )


def test_check_rejects_unpublished_sha256_claim(tmp_path):
    copy_documentation(tmp_path)
    release = tmp_path / "release.json"
    metadata = json.loads(release.read_text(encoding="utf-8"))
    metadata["capabilities"]["sha256ArchiveVerification"] = False
    release.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8") + "\nUse AI_COCKPIT_TEMPLATE_SHA256 for verification.\n",
        encoding="utf-8",
    )

    assert any(
        "SHA256 verification is not published" in error for error in check_repository(tmp_path)
    )


def test_check_rejects_concrete_or_missing_readme_release_resolution(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        .replace("main/release.json", "release-metadata-missing")
        .replace("${RELEASE_TAG}/install.sh", "v9.9.9/install.sh"),
        encoding="utf-8",
    )

    errors = check_repository(tmp_path)
    assert "README.md: primary README must not hardcode a concrete release version" in errors
    assert (
        "README.md: primary install command must resolve the tagged installer from release.json"
        in errors
    )


def test_check_rejects_known_japanese_style_regressions(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.ja.md"
    regression_line = (
        "\nGemini, Claude, Codex "
        "\u306b\u3088\u308a\u5b9f\u884c\u6642\u306e\u5b89\u5168\u6027\u3092\u78ba\u4fdd\u3057\u3001"
        "\u78ba\u4fe1\u5ea6\u3092\u8a18\u9332\u3057\u307e\u3059\u3002\n"
    )
    readme.write_text(readme.read_text(encoding="utf-8") + regression_line, encoding="utf-8")

    errors = check_repository(tmp_path)
    assert sum("Japanese style:" in error for error in errors) == 3
