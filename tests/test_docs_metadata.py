import json
import shutil
from pathlib import Path

from check_docs_metadata import (
    beginner_installation_errors,
    check_repository,
    command_evidence_errors,
    documentation_architecture_errors,
    documentation_fact_errors,
    formal_document_metadata_errors,
    front_matter_errors,
    historical_context_errors,
    installation_command_errors,
    multilingual_layer_errors,
    stack_errors,
)

ROOT = Path(__file__).resolve().parents[1]


def test_ordinary_docs_metadata_does_not_import_release_alignment_gate():
    source = (ROOT / "scripts" / "check_docs_metadata.py").read_text(encoding="utf-8")

    assert "check_pre_release_documentation_alignment" not in source


def copy_documentation(target: Path) -> None:
    for name in ("README.md", "README.ja.md", "README.zh-CN.md"):
        shutil.copy2(ROOT / name, target / name)
    shutil.copytree(ROOT / "docs", target / "docs")
    shutil.copytree(ROOT / "examples", target / "examples")
    (target / ".ai").mkdir()
    shutil.copy2(ROOT / ".ai" / "README.md", target / ".ai" / "README.md")
    shutil.copy2(ROOT / ".ai" / "glossary.md", target / ".ai" / "glossary.md")
    shutil.copy2(ROOT / "release.json", target / "release.json")
    shutil.copy2(ROOT / "next-release.json", target / "next-release.json")
    shutil.copy2(ROOT / "install.sh", target / "install.sh")
    shutil.copy2(ROOT / "Makefile", target / "Makefile")


def test_repository_documentation_metadata_is_consistent():
    assert check_repository(ROOT) == []


def test_wi07_documentation_architecture_is_complete():
    assert formal_document_metadata_errors(ROOT) == []
    assert documentation_architecture_errors(ROOT) == []


def test_wi07_formal_metadata_rejects_missing_and_invalid_values(tmp_path):
    copy_documentation(tmp_path)
    path = tmp_path / "docs" / "concepts" / "decision-states.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("status: current", "status: obsolete", 1).replace(
            "lastVerifiedBy: capability-truth-matrix\n", "", 1
        ),
        encoding="utf-8",
    )

    errors = formal_document_metadata_errors(tmp_path)
    assert "docs/concepts/decision-states.md: invalid status: obsolete" in errors
    assert "docs/concepts/decision-states.md: front matter missing lastVerifiedBy" in errors


def test_wi07_architecture_rejects_missing_topic_and_extra_readme_section(tmp_path):
    copy_documentation(tmp_path)
    (tmp_path / "docs" / "security" / "threat-model.md").unlink()
    readme = tmp_path / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + "\n<!-- readme-section: release-internals -->\n## Release internals\n",
        encoding="utf-8",
    )

    errors = documentation_architecture_errors(tmp_path)
    assert "docs/security/threat-model.md: required WI07 canonical document is missing" in errors
    assert "README.md: unsupported README section marker: release-internals" in errors


def test_wi07_archive_entrypoints_are_historical_not_runtime_instructions(tmp_path):
    copy_documentation(tmp_path)
    archive = tmp_path / "docs" / "archive" / "plans" / "README.md"
    archive.write_text(
        archive.read_text(encoding="utf-8").replace("status: historical", "status: current"),
        encoding="utf-8",
    )

    errors = formal_document_metadata_errors(tmp_path)
    assert "docs/archive/plans/README.md: expected status historical, found current" in errors


def test_trilingual_beginner_routes_are_complete():
    assert beginner_installation_errors(ROOT) == []


def test_existing_layer_and_command_checks_remain_complete():
    assert multilingual_layer_errors(ROOT) == []
    assert command_evidence_errors(ROOT) == []
    assert documentation_fact_errors(ROOT) == []
    assert historical_context_errors(ROOT) == []


def test_beginner_route_rejects_missing_work_item_handoff_and_internal_mechanics(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.zh-CN.md"
    installation.write_text(
        installation.read_text(encoding="utf-8").replace(
            "安装完成后，开始独立的工程校准 Work Item。",
            "安装完成后，请阅读 Candidate、phase record 和 Session schema。",
            1,
        ),
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/installation.zh-CN.md: missing post-install Work Item handoff"
        in errors
    )
    assert (
        "docs/getting-started/installation.zh-CN.md: internal calibration mechanics belong in the reference route"
        in errors
    )


def test_beginner_route_rejects_missing_separated_route(tmp_path):
    copy_documentation(tmp_path)
    (tmp_path / "docs/troubleshooting/installation.ja.md").unlink()

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/troubleshooting/installation.ja.md: required separated installation route is missing"
        in errors
    )


def test_beginner_route_rejects_missing_home_page_and_readme_entry(tmp_path):
    copy_documentation(tmp_path)
    (tmp_path / "docs/getting-started/installation.ja.md").unlink()
    readme = tmp_path / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "docs/getting-started/installation.md", "docs/getting-started/start-here.md"
        ),
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/installation.ja.md: required beginner installation guide is missing"
        in errors
    )
    assert (
        "README.md: missing same-language beginner installation entry: docs/getting-started/installation.md"
        in errors
    )


def test_beginner_route_rejects_oversized_home_page(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.md"
    installation.write_text(
        installation.read_text(encoding="utf-8") + ("\nMore detail." * 261),
        encoding="utf-8",
    )

    assert (
        "docs/getting-started/installation.md: beginner page exceeds 260 lines"
        in beginner_installation_errors(tmp_path)
    )


def test_beginner_route_rejects_lost_safety_boundary(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.ja.md"
    installation.write_text(
        installation.read_text(encoding="utf-8").replace("Unknown", "不明"),
        encoding="utf-8",
    )

    assert (
        "docs/getting-started/installation.ja.md: missing Unknown stop boundary"
        in beginner_installation_errors(tmp_path)
    )


def test_beginner_route_rejects_lost_advanced_link_and_authority_boundary(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.md"
    installation.write_text(
        installation.read_text(encoding="utf-8")
        .replace("calibration.md", "calibration-guide.md")
        .replace("commit", "record")
        .replace("push", "send")
        .replace("pull request", "review request"),
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)
    assert (
        "docs/getting-started/installation.md: missing route link: docs/getting-started/calibration.md"
        in errors
    )
    assert "docs/getting-started/installation.md: missing separated authority boundary" in errors


def test_beginner_route_rejects_missing_platform_examples(tmp_path):
    copy_documentation(tmp_path)
    installation = tmp_path / "docs/getting-started/installation.md"
    installation.write_text(
        installation.read_text(encoding="utf-8").replace(
            "examples/android.md", "examples/mobile.md"
        ),
        encoding="utf-8",
    )

    assert (
        "docs/getting-started/installation.md: missing platform example route"
        in beginner_installation_errors(tmp_path)
    )


def test_beginner_route_rejects_platform_page_without_work_item_entry(tmp_path):
    copy_documentation(tmp_path)
    platform_page = tmp_path / "docs/getting-started/examples/ios.zh-CN.md"
    platform_page.write_text(
        platform_page.read_text(encoding="utf-8").replace(
            "<!-- platform-entry: work-item-first -->",
            "<!-- platform-entry: removed -->",
            1,
        ),
        encoding="utf-8",
    )

    assert (
        "docs/getting-started/examples/ios.zh-CN.md: missing Work Item-first platform entry"
        in beginner_installation_errors(tmp_path)
    )


def test_beginner_route_rejects_platform_page_without_calibration_and_recovery_route(tmp_path):
    copy_documentation(tmp_path)
    platform_page = tmp_path / "docs/getting-started/examples/android.ja.md"
    platform_page.write_text(
        platform_page.read_text(encoding="utf-8").replace(
            "<!-- platform-next: calibration-and-recovery -->",
            "<!-- platform-next: removed -->",
            1,
        ),
        encoding="utf-8",
    )

    assert (
        "docs/getting-started/examples/android.ja.md: missing calibration and recovery route"
        in beginner_installation_errors(tmp_path)
    )


def test_beginner_route_rejects_platform_page_without_evidence_boundary_or_with_legacy_flow(
    tmp_path,
):
    copy_documentation(tmp_path)
    platform_page = tmp_path / "docs/getting-started/examples/java.md"
    platform_page.write_text(
        platform_page.read_text(encoding="utf-8").replace(
            "<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->",
            "<!-- platform-boundary: removed -->",
            1,
        )
        + "\n<!-- platform-stage: legacy -->\n",
        encoding="utf-8",
    )

    errors = beginner_installation_errors(tmp_path)
    assert "docs/getting-started/examples/java.md: missing platform evidence boundary" in errors
    assert (
        "docs/getting-started/examples/java.md: contains legacy seven-stage platform flow" in errors
    )


def test_java_multimodule_maven_correction_template_preserves_safety_boundaries():
    expected_markers = {
        "java.md": ("reactor command", "settings.xml", "actual `java`", "**blocked**"),
        "java.ja.md": ("reactor command", "settings.xml", "actual major", "**blocked**"),
        "java.zh-CN.md": ("reactor command", "settings.xml", "actual major", "**blocked**"),
    }

    for name, markers in expected_markers.items():
        text = (ROOT / "docs" / "getting-started" / "examples" / name).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text
        assert "private repository URL" in " ".join(text.split())
        assert "does not" in text or "しません" in text or "不会" in text


def test_java_guidance_configures_runtime_lane_validation_without_managing_a_jdk():
    expected_markers = {
        "java.md": ("AI_COCKPIT_JAVA_LANE", "AI_COCKPIT_JAVA_REQUIRED_MAJOR", "JAVA_HOME"),
        "java.ja.md": ("AI_COCKPIT_JAVA_LANE", "AI_COCKPIT_JAVA_REQUIRED_MAJOR", "JAVA_HOME"),
        "java.zh-CN.md": ("AI_COCKPIT_JAVA_LANE", "AI_COCKPIT_JAVA_REQUIRED_MAJOR", "JAVA_HOME"),
    }

    for name, markers in expected_markers.items():
        text = (ROOT / "docs" / "getting-started" / "examples" / name).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text
        assert "install" in text or "インストール" in text or "安装" in text


def test_layer_checker_rejects_missing_language_document(tmp_path):
    copy_documentation(tmp_path)
    (tmp_path / "docs/getting-started/30-second-start.ja.md").unlink()

    assert (
        "docs/getting-started/30-second-start.ja.md: required WI-10 language document is missing"
        in multilingual_layer_errors(tmp_path)
    )


def test_command_checker_rejects_unknown_evidence_label(tmp_path):
    copy_documentation(tmp_path)
    start = tmp_path / "docs/getting-started/30-second-start.zh-CN.md"
    start.write_text(
        start.read_text(encoding="utf-8").replace(
            "<!-- command-evidence: adopter_required -->",
            "<!-- command-evidence: unsupported_claim -->",
            1,
        ),
        encoding="utf-8",
    )

    assert any(
        "unknown command evidence label: unsupported_claim" in error
        for error in command_evidence_errors(tmp_path)
    )


def test_documentation_facts_reject_unsupported_ui_claim(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8") + "\nJapanese is the default UI locale.\n",
        encoding="utf-8",
    )

    assert any(
        "Japanese is the default UI locale" in error
        for error in documentation_fact_errors(tmp_path)
    )


def test_context_registry_rejects_missing_or_invalid_registry(tmp_path):
    copy_documentation(tmp_path)
    registry = tmp_path / "docs/reference/documentation-context-registry.json"
    registry.unlink()
    assert historical_context_errors(tmp_path) == [
        "docs/reference/documentation-context-registry.json: missing context registry"
    ]

    registry.write_text("{", encoding="utf-8")
    assert historical_context_errors(tmp_path) == [
        "docs/reference/documentation-context-registry.json: invalid JSON"
    ]


def test_context_registry_rejects_missing_governed_entry_and_archive_classification(tmp_path):
    copy_documentation(tmp_path)
    registry = tmp_path / "docs/reference/documentation-context-registry.json"
    value = json.loads(registry.read_text(encoding="utf-8"))
    value["entries"] = [
        entry
        for entry in value["entries"]
        if entry["path"] != ".ai/work-items/archive/**"
        and entry["path"]
        != "docs/superpowers/plans/2026-07-30-wi10-installation-information-architecture.md"
    ]
    registry.write_text(json.dumps(value), encoding="utf-8")

    errors = historical_context_errors(tmp_path)
    assert (
        ".ai/work-items/archive/**: immutable historical archive classification is missing"
        in errors
    )
    assert (
        "docs/superpowers/plans/2026-07-30-wi10-installation-information-architecture.md: "
        "missing from documentation context registry"
    ) in errors


def test_context_registry_rejects_invalid_schema_entries_and_mutable_history(tmp_path):
    copy_documentation(tmp_path)
    registry = tmp_path / "docs/reference/documentation-context-registry.json"
    value = json.loads(registry.read_text(encoding="utf-8"))
    value["schemaVersion"] = 2
    value["entries"] = [
        None,
        {
            "path": "docs/reference/documentation-architecture.md",
            "context": "invalid",
            "mutable": "yes",
        },
        {
            "path": "docs/reference/documentation-architecture.md",
            "context": "historical_record",
            "mutable": True,
        },
        {"path": ".ai/work-items/archive/**", "context": "historical_record", "mutable": False},
    ]
    registry.write_text(json.dumps(value), encoding="utf-8")

    errors = historical_context_errors(tmp_path)
    assert "docs/reference/documentation-context-registry.json: schemaVersion must be 1" in errors
    assert "documentation context entry 0 must be an object" in errors
    assert (
        "documentation context path has invalid context: docs/reference/documentation-architecture.md"
        in errors
    )
    assert (
        "documentation context path requires boolean mutable: docs/reference/documentation-architecture.md"
        in errors
    )
    assert (
        "documentation context path is duplicated: docs/reference/documentation-architecture.md"
        in errors
    )
    assert (
        "docs/reference/documentation-architecture.md: missing historical context marker" in errors
    )


def test_front_matter_and_stack_checks_reject_missing_required_metadata(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("title: incomplete\n", encoding="utf-8")
    assert str(readme) + ": missing YAML front matter" in front_matter_errors(readme)

    readme.write_text("---\ntitle: incomplete\n", encoding="utf-8")
    assert str(readme) + ": unterminated YAML front matter" in front_matter_errors(readme)

    stack_root = tmp_path / "stack"
    stack_root.mkdir()
    copy_documentation(stack_root)
    configuration = stack_root / "docs" / "configuration.md"
    configuration.write_text(
        configuration.read_text(encoding="utf-8").replace("generic\nrust", "generic only"),
        encoding="utf-8",
    )
    assert (
        "docs/configuration.md: supported-stack list does not match installer STACKS"
        in stack_errors(stack_root)
    )


def test_installation_command_check_rejects_missing_primary_contract_markers(tmp_path):
    copy_documentation(tmp_path)
    quick_start = tmp_path / "docs" / "getting-started" / "30-second-start.md"
    quick_start.write_text(
        quick_start.read_text(encoding="utf-8")
        .replace("main/release.json", "release.json")
        .replace("$RELEASE_TAG/install.sh", "install.sh")
        .replace(
            "https://github.com/spirex-ds-dev/ai-cockpit-template.git",
            "https://example.invalid/repo.git",
        )
        .replace("--interactive", "--dry-run"),
        encoding="utf-8",
    )

    errors = installation_command_errors(tmp_path)
    assert (
        "docs/getting-started/30-second-start.md: quick start must resolve the tagged installer from release.json"
        in errors
    )
    assert (
        "docs/getting-started/30-second-start.md: canonical public source default is missing: https://github.com/spirex-ds-dev/ai-cockpit-template.git"
        in errors
    )
    assert "docs/getting-started/30-second-start.md: wizard entry is missing" in errors


def test_installation_command_check_distinguishes_audit_history_from_current_release_claims(
    tmp_path,
):
    copy_documentation(tmp_path)

    errors = installation_command_errors(tmp_path)
    assert not any(error.startswith("docs/audits/") for error in errors)

    current_claim = tmp_path / "docs" / "reference" / "current-release-claim.md"
    current_claim.write_text("The current installer release is v0.5.42.\n", encoding="utf-8")

    errors = installation_command_errors(tmp_path)
    assert (
        "docs/reference/current-release-claim.md:1: documented release v0.5.42 does not "
        "match release.json v0.5.56"
    ) in errors
