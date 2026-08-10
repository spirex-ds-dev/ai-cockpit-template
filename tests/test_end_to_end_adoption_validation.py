import json
import subprocess
import sys
from pathlib import Path

import end_to_end_adoption_validation as validation

ROOT = Path(__file__).resolve().parents[1]


def test_root_pytest_collection_excludes_adopter_fixture_tests():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "examples/fixtures/python/tests/test_service.py" not in result.stdout
    assert "examples/fixtures/mixed-monorepo/services/api/tests/test_app.py" not in result.stdout


def test_fixture_catalog_contains_the_seven_required_real_project_shapes():
    fixtures = validation.discover_fixtures(ROOT / "examples" / "fixtures")

    assert {item.project_type for item in fixtures} == {
        "python-service",
        "typescript-web-application",
        "java-backend",
        "android-application",
        "ios-swift-package",
        "flutter-application",
        "mixed-monorepo",
    }
    for fixture in fixtures:
        assert fixture.safe_change_path.is_file()
        assert fixture.test_path.is_file()
        assert fixture.installer_stack in validation.INSTALLER_STACKS


def test_immutable_fixture_cache_is_tree_digest_bound_and_targets_are_isolated(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("value = 1\n", encoding="utf-8")
    (source / "test_app.py").write_text("def test_value(): pass\n", encoding="utf-8")
    fixture = validation.Fixture(
        root=source,
        project_type="python-service",
        stack="python",
        installer_stack="python",
        toolchain="python",
        platforms=(),
        safe_change_path=source / "app.py",
        test_path=source / "test_app.py",
    )

    immutable = validation.prepare_immutable_fixture(fixture, tmp_path / "cache")
    first, second = tmp_path / "first", tmp_path / "second"
    validation.copy_immutable_fixture(immutable, first)
    validation.copy_immutable_fixture(immutable, second)
    (first / "app.py").write_text("value = 2\n", encoding="utf-8")

    assert immutable.name.startswith("python-service-")
    assert (immutable / "app.py").read_text(encoding="utf-8") == "value = 1\n"
    assert (second / "app.py").read_text(encoding="utf-8") == "value = 1\n"


def test_policy_probes_fail_closed_without_promoting_warnings_or_missing_evidence():
    probes = validation.run_policy_probes()

    assert {probe["id"] for probe in probes} == {
        "delete-referenced-function",
        "external-markdown-injection",
        "forged-approval",
        "fabricated-test-success",
    }
    assert all(probe["status"] == "blocked" for probe in probes)
    assert all(probe["evidenceKind"] == "policy_probe" for probe in probes)
    assert all(probe["recovery"] for probe in probes)


def test_complete_matrix_executes_real_local_lifecycle_and_failure_cases(tmp_path):
    bundle = validation.run_validation(ROOT, workspace=tmp_path)

    assert bundle["schemaVersion"] == 1
    assert len(bundle["fixtures"]) == 7
    required = set(validation.LIFECYCLE_PHASES)
    for fixture in bundle["fixtures"]:
        phases = {item["phase"]: item for item in fixture["phases"]}
        assert set(phases) == required
        assert phases["install"]["status"] == "passed"
        assert phases["calibrate"]["status"] == "passed"
        assert phases["finish"]["status"] == "passed"
        assert phases["pr_evidence"]["evidenceKind"] == "local_provider_simulation"
        assert phases["close_work_item"]["status"] == "passed"
        assert phases["upgrade"]["status"] == "passed"
        assert "projectProfilePreserved=true" in phases["upgrade"]["evidence"]
        assert phases["failed_upgrade_rollback"]["status"] == "passed"
        assert "stateRestored=true" in phases["failed_upgrade_rollback"]["evidence"]
        assert phases["scope_violation"]["status"] == "blocked"
        assert phases["test_deletion"]["status"] == "blocked"
        assert phases["test_skip"]["status"] == "blocked"
        assert phases["coverage_weakening"]["status"] == "blocked"
        assert phases["external_markdown_injection"]["status"] == "blocked"
        assert phases["forged_approval"]["status"] == "blocked"
        assert phases["fabricated_test_success"]["status"] == "blocked"
        assert fixture["repositoryState"] == {
            "branch": "main",
            "clean": True,
            "workBranches": [],
            "remoteWorkBranches": [],
        }

    failures = {item["case"]: item for item in bundle["installationFailures"]}
    assert set(failures) == {
        "dirty_worktree",
        "marker_conflict",
        "makefile_conflict",
        "detached_head",
        "network_unavailable",
        "invalid_release_metadata",
    }
    assert all(item["status"] == "blocked" for item in failures.values())
    assert all(item["stateRestored"] is True for item in failures.values())
    assert bundle["evidenceBoundary"] == {
        "hostedProvider": "not_run",
        "providerIdentity": "not_run",
        "deviceAndSigning": "not_run",
        "enterpriseAssurance": "not_claimed",
    }


def test_cli_writes_the_same_reviewable_json_shape(tmp_path):
    output = tmp_path / "validation.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/end_to_end_adoption_validation.py",
            "--root",
            str(ROOT),
            "--output",
            str(output),
            "--catalog-only",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schemaVersion"] == 1
    assert len(payload["fixtures"]) == 7
    assert payload["mode"] == "catalog_only"
