import json
from pathlib import Path

import pytest

from scripts.ai_install_facts import digest_file, write_fact_bundle
from scripts.ai_uninstall_facts import UninstallFactsError, collect_uninstall_facts


def installed_repository(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    root = tmp_path / "adopter"
    (source / "scripts").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)
    (source / "scripts/runtime.py").write_text("runtime\n", encoding="utf-8")
    (root / "scripts/runtime.py").write_text("runtime\n", encoding="utf-8")
    (root / "README.md").write_text("project\n", encoding="utf-8")
    write_fact_bundle(
        source=source,
        target=root,
        distribution_version={
            "distributionVersion": "test",
            "releaseVersion": "test",
            "contractSchema": 2,
        },
    )
    return root


def test_facts_are_deterministic_and_only_unchanged_source_managed_files_are_removable(
    tmp_path,
):
    root = installed_repository(tmp_path)

    first = collect_uninstall_facts(root, "session-1")
    second = collect_uninstall_facts(root, "session-1")

    assert first == second
    assert first["state"] == "ready"
    assert first["runtimeFiles"] == [
        {
            "path": "scripts/runtime.py",
            "digest": digest_file(root / "scripts/runtime.py"),
            "ownership": "template",
            "type": "file",
        }
    ]
    assert "README.md" in first["preservePaths"]
    assert first["repositoryIdentity"].startswith("sha256:")


def test_modified_managed_file_fails_closed(tmp_path):
    root = installed_repository(tmp_path)
    (root / "scripts/runtime.py").write_text("changed\n", encoding="utf-8")

    with pytest.raises(UninstallFactsError, match="drift"):
        collect_uninstall_facts(root, "session-1")


def test_manifest_path_escape_fails_before_bundle_validation(tmp_path):
    root = installed_repository(tmp_path)
    manifest_path = root / ".ai/install/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["path"] = "../outside.txt"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(UninstallFactsError, match="unsafe managed path"):
        collect_uninstall_facts(root, "session-1")


def test_symlinked_runtime_or_parent_fails_closed(tmp_path):
    root = installed_repository(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("runtime\n", encoding="utf-8")
    runtime = root / "scripts/runtime.py"
    runtime.unlink()
    runtime.symlink_to(outside)

    with pytest.raises(UninstallFactsError, match="symlink"):
        collect_uninstall_facts(root, "session-1")
