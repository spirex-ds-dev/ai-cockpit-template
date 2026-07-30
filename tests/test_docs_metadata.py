import json
import shutil
from pathlib import Path

from check_docs_metadata import (
    beginner_installation_errors,
    check_repository,
    command_evidence_errors,
    documentation_fact_errors,
    historical_context_errors,
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
