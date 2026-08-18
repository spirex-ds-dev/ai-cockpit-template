from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import ai_installer_adopter_capability_manifest as capability_manifest
from install_ai_cockpit import Installer

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / ".ai" / "project" / "adopter-capability-manifest.json"
MANIFEST_SCHEMA_PATH = ROOT / ".ai" / "schemas" / "adopter-capability-manifest.schema.json"
CATALOG_PATH = ROOT / "scripts" / "ai_installer_catalog.json"


def load_manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def make_targets(path: Path) -> set[str]:
    return set(
        re.findall(r"^([A-Za-z0-9_.-]+):(?!=)", path.read_text(encoding="utf-8"), re.MULTILINE)
    )


def assert_no_nulls(value: object, path: str = "manifest") -> None:
    if value is None:
        raise AssertionError(f"{path} must not be null")
    if isinstance(value, dict):
        for key, child in value.items():
            assert_no_nulls(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_nulls(child, f"{path}[{index}]")


def test_adopter_capability_manifest_declares_a_closed_installation_surface() -> None:
    manifest = load_manifest()

    assert manifest["schemaVersion"] == 2
    assert manifest["schemaFile"] == ".ai/schemas/adopter-capability-manifest.schema.json"
    assert MANIFEST_SCHEMA_PATH.is_file()
    assert_no_nulls(manifest)
    assert manifest["capabilities"]
    assert manifest["exclusions"]
    required = {
        "id",
        "adopterFacing",
        "status",
        "ownership",
        "truth",
        "templateFiles",
        "installedFiles",
        "makeTargets",
        "schemas",
        "entrypoints",
        "docs",
        "verifyInstalledSurface",
    }
    for capability in manifest["capabilities"]:
        assert required <= capability.keys(), capability
        assert capability["adopterFacing"] is True
        assert capability["status"] in {
            "implemented",
            "template_only",
            "adopter_installed",
            "planned",
        }
        assert capability["truth"] == capability["status"]
        assert capability["ownership"] in manifest["ownershipVocabulary"]
        assert capability["templateFiles"], capability["id"]
        if capability["verifyInstalledSurface"]:
            assert capability["installedFiles"], capability["id"]
            assert capability["makeTargets"], capability["id"]
            assert capability["schemas"], capability["id"]

    exclusions_required = {
        "id",
        "adopterFacing",
        "status",
        "ownership",
        "exclusionType",
        "reason",
        "templateFiles",
        "installedFiles",
        "makeTargets",
        "schemas",
        "docs",
    }
    for exclusion in manifest["exclusions"]:
        assert exclusions_required <= exclusion.keys(), exclusion
        assert exclusion["adopterFacing"] is False
        assert exclusion["status"] == "excluded"
        assert exclusion["exclusionType"] in {"external", "template_only"}
        assert exclusion["ownership"] in manifest["ownershipVocabulary"]


def test_manifest_schema_is_strict_and_requires_a_non_null_capability_surface() -> None:
    schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert {
        "schemaVersion",
        "schemaFile",
        "manifestId",
        "statusVocabulary",
        "ownershipVocabulary",
        "capabilityTruthRule",
        "capabilities",
        "exclusions",
    } <= set(schema["required"])
    capability_schema = schema["$defs"]["capability"]
    assert capability_schema["additionalProperties"] is False
    assert {
        "id",
        "adopterFacing",
        "status",
        "ownership",
        "templateFiles",
        "installedFiles",
        "makeTargets",
        "schemas",
        "entrypoints",
        "docs",
    } <= set(capability_schema["required"])


def test_implementation_approach_reserves_current_report_surface_without_claiming_it() -> None:
    capabilities = {item["id"]: item for item in load_manifest()["capabilities"]}
    reserved = capabilities["implementation_approach_report"]
    current = capabilities["implementation_knowledge_reports"]

    assert reserved["status"] == "adopter_installed"
    assert reserved["surfaceRole"] == "reserved_reference"
    assert reserved["reservedSurfaceFrom"] == "implementation_knowledge_reports"
    assert set(reserved["templateFiles"]) <= set(current["templateFiles"])
    assert set(reserved["installedFiles"]) <= set(current["installedFiles"])
    assert set(reserved["makeTargets"]) <= set(current["makeTargets"])
    assert set(reserved["schemas"]) <= set(current["schemas"])
    assert {item["path"] for item in reserved["entrypoints"]} <= {
        item["path"] for item in current["entrypoints"]
    }


def test_performance_diagnosis_has_an_independent_declared_surface() -> None:
    capabilities = {item["id"]: item for item in load_manifest()["capabilities"]}
    governance = capabilities["governance_cost_metrics"]
    performance = capabilities["performance_diagnosis"]

    assert performance["makeTargets"] == ["ai-performance-diagnosis"]
    assert performance["schemas"] == [".ai/schemas/performance-diagnosis-report.schema.json"]
    assert performance["docs"] == ["docs/reference/performance-diagnosis.md"]
    assert "ai-performance-diagnosis" not in governance["makeTargets"]
    assert ".ai/schemas/performance-diagnosis-report.schema.json" not in governance["schemas"]


def test_manifest_capability_scripts_are_in_installer_catalog() -> None:
    manifest = load_manifest()
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog_scripts = set(catalog["scripts"])

    for capability in manifest["capabilities"]:
        for script in capability["catalogScripts"]:
            assert script in catalog_scripts, f"{capability['id']}: {script}"


def test_manifest_make_targets_are_in_source_and_installed_makefiles() -> None:
    manifest = load_manifest()
    required_targets = {
        target for capability in manifest["capabilities"] for target in capability["makeTargets"]
    }

    source_targets = make_targets(ROOT / "Makefile")
    installed_targets = make_targets(ROOT / "templates" / "make" / "Makefile.ai")
    assert required_targets <= source_targets
    assert required_targets <= installed_targets


def test_fresh_empty_adopter_installs_and_executes_declared_capabilities(tmp_path: Path) -> None:
    target = tmp_path / "adopter"
    target.mkdir()
    manifest = load_manifest()
    installer = Installer(
        source=ROOT,
        target=target,
        stack="generic",
        force=False,
        dry_run=False,
        with_examples=False,
        update_makefile=True,
    )

    assert installer.install() == 0
    installed_makefile = target / "Makefile.ai"
    installed_text = installed_makefile.read_text(encoding="utf-8")
    manifest_check = subprocess.run(
        [
            sys.executable,
            str(target / "scripts" / "ai_installer_adopter_capability_manifest.py"),
            "--root",
            str(target),
            "--installed",
        ],
        cwd=target,
        text=True,
        capture_output=True,
        check=False,
    )
    assert manifest_check.returncode == 0, (manifest_check.stdout, manifest_check.stderr)

    for capability in manifest["capabilities"]:
        if not capability["verifyInstalledSurface"]:
            continue
        for relative in capability["installedFiles"]:
            assert (target / relative).is_file(), f"{capability['id']}: {relative}"
        for schema in capability["schemas"]:
            assert (target / schema).is_file(), f"{capability['id']}: {schema}"
        for make_target in capability["makeTargets"]:
            assert re.search(rf"^{re.escape(make_target)}:", installed_text, re.MULTILINE)
        for entrypoint in capability["entrypoints"]:
            result = subprocess.run(
                [
                    sys.executable,
                    str(target / entrypoint["path"]),
                    *entrypoint["args"],
                ],
                cwd=target,
                text=True,
                capture_output=True,
                check=False,
            )
            assert result.returncode == 0, (
                capability["id"],
                entrypoint,
                result.stdout,
                result.stderr,
            )


def test_manifest_validator_fails_closed_for_missing_required_field(tmp_path: Path) -> None:
    manifest = load_manifest()
    del manifest["capabilities"][0]["ownership"]
    broken = tmp_path / "broken-manifest.json"
    broken.write_text(json.dumps(manifest), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "ai_installer_adopter_capability_manifest.py"),
            "--root",
            str(ROOT),
            "--manifest",
            str(broken),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "ownership" in result.stderr


def test_manifest_validator_entrypoint_regression_checks_real_installed_surface(
    tmp_path: Path,
) -> None:
    target = tmp_path / "adopter"
    target.mkdir()
    installer = Installer(
        source=ROOT,
        target=target,
        stack="generic",
        force=False,
        dry_run=False,
        with_examples=False,
        update_makefile=True,
    )

    assert installer.install() == 0
    checker = target / "scripts" / "ai_installer_adopter_capability_manifest.py"
    assert capability_manifest.main(["--root", str(target), "--installed"]) == 0

    installed_manifest = load_manifest()
    installed_manifest["capabilities"][0]["installedFiles"].append(
        "scripts/missing-installed-capability-file.py"
    )
    installed_mismatch = tmp_path / "installed-mismatch.json"
    installed_mismatch.write_text(json.dumps(installed_manifest), encoding="utf-8")
    assert (
        capability_manifest.main(
            [
                "--root",
                str(target),
                "--manifest",
                str(installed_mismatch),
                "--installed",
            ]
        )
        == 1
    )

    result = subprocess.run(
        [sys.executable, str(checker), "--root", str(target), "--installed"],
        cwd=target,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "adopter capability manifest valid" in result.stdout


def test_manifest_validator_module_covers_source_and_fail_closed_paths(
    tmp_path: Path,
) -> None:
    assert capability_manifest.main(["--root", str(ROOT)]) == 0

    manifest = load_manifest()
    manifest["schemaVersion"] = 1
    wrong_version = tmp_path / "wrong-version.json"
    wrong_version.write_text(json.dumps(manifest), encoding="utf-8")
    assert capability_manifest.main(["--root", str(ROOT), "--manifest", str(wrong_version)]) == 1

    manifest = load_manifest()
    manifest["capabilities"] = "not-an-array"
    malformed_capabilities = tmp_path / "malformed-capabilities.json"
    malformed_capabilities.write_text(json.dumps(manifest), encoding="utf-8")
    assert (
        capability_manifest.main(["--root", str(ROOT), "--manifest", str(malformed_capabilities)])
        == 1
    )

    manifest = load_manifest()
    manifest["exclusions"] = []
    missing_exclusions = tmp_path / "missing-exclusions.json"
    missing_exclusions.write_text(json.dumps(manifest), encoding="utf-8")
    assert (
        capability_manifest.main(["--root", str(ROOT), "--manifest", str(missing_exclusions)]) == 1
    )

    manifest = load_manifest()
    del manifest["schemaFile"]
    missing_root_field = tmp_path / "missing-root-field.json"
    missing_root_field.write_text(json.dumps(manifest), encoding="utf-8")
    assert (
        capability_manifest.main(["--root", str(ROOT), "--manifest", str(missing_root_field)]) == 1
    )

    manifest = load_manifest()
    manifest["capabilities"][0]["templateFiles"] = ["../unsafe-template.json"]
    unsafe_template = tmp_path / "unsafe-template.json"
    unsafe_template.write_text(json.dumps(manifest), encoding="utf-8")
    assert capability_manifest.main(["--root", str(ROOT), "--manifest", str(unsafe_template)]) == 1
