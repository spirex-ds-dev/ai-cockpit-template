import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import quality_test_manifest


def _entry(entry_id: str, duration: int, kind: str = "pytest") -> dict[str, object]:
    return {"id": entry_id, "durationMs": duration, "kind": kind}


def _receipt(shard: str, **overrides: object) -> dict[str, object]:
    receipt: dict[str, object] = {
        "shard": shard,
        "commitSha": "a" * 40,
        "treeDigest": "sha256:" + "b" * 64,
        "result": "passed",
        "artifacts": {
            "junit": f"{shard}.xml",
            "coverage": f"{shard}.coverage",
            "coverageData": f"{shard}.coverage-data",
            "timing": f"{shard}.json",
            "gateLog": f"{shard}.log",
            "receipt": f"{shard}.receipt.json",
        },
    }
    receipt.update(overrides)
    return receipt


def test_assign_shards_uses_duration_balancing_and_exactly_one_owner():
    assignments = quality_test_manifest.assign_shards(
        [_entry("slow", 100), _entry("medium", 60), _entry("fast-a", 20), _entry("fast-b", 20)],
        ["core", "governance"],
    )

    assert assignments == {"core": ["slow"], "governance": ["medium", "fast-a", "fast-b"]}
    assert (
        quality_test_manifest.validate_assignments(
            [_entry("slow", 100), _entry("medium", 60), _entry("fast-a", 20), _entry("fast-b", 20)],
            assignments,
        )
        is None
    )


def test_validate_assignments_rejects_missing_duplicate_and_unknown_entries():
    entries = [_entry("a", 10), _entry("b", 20)]
    with pytest.raises(quality_test_manifest.ManifestError, match="unowned"):
        quality_test_manifest.validate_assignments(entries, {"core": ["a"]})
    with pytest.raises(quality_test_manifest.ManifestError, match="more than one"):
        quality_test_manifest.validate_assignments(
            entries, {"core": ["a", "b"], "governance": ["a"]}
        )
    with pytest.raises(quality_test_manifest.ManifestError, match="unknown"):
        quality_test_manifest.validate_assignments(entries, {"core": ["a", "b", "gone"]})


def test_validate_aggregate_rejects_each_missing_artifact_and_wrong_source():
    expected_source = {"commitSha": "a" * 40, "treeDigest": "sha256:" + "b" * 64}
    valid = [_receipt("core"), _receipt("governance")]
    assert (
        quality_test_manifest.validate_aggregate(valid, ["core", "governance"], expected_source)
        is None
    )

    for artifact in ("junit", "coverage", "coverageData", "timing", "gateLog", "receipt"):
        broken = _receipt("core")
        artifacts = dict(broken["artifacts"])
        del artifacts[artifact]
        broken["artifacts"] = artifacts
        with pytest.raises(quality_test_manifest.ManifestError, match=artifact):
            quality_test_manifest.validate_aggregate(
                [broken, _receipt("governance")], ["core", "governance"], expected_source
            )

    with pytest.raises(quality_test_manifest.ManifestError, match="commitSha"):
        quality_test_manifest.validate_aggregate(
            [_receipt("core", commitSha="c" * 40), _receipt("governance")],
            ["core", "governance"],
            expected_source,
        )


def test_run_shard_receipt_records_comparable_runner_and_cache_facts(tmp_path, monkeypatch):
    root = tmp_path / "repository"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True
    )
    (root / "tracked.txt").write_text("source\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "source"], check=True)
    monkeypatch.setenv("ImageOS", "ubuntu24")
    monkeypatch.setenv("ImageVersion", "20260801.1")
    monkeypatch.setenv("RUNNER_OS", "Linux")

    receipt = quality_test_manifest.run_shard(
        root,
        {
            "schemaVersion": 1,
            "entries": [{"id": "shell:pass.sh", "kind": "shell", "stage": "shard"}],
        },
        {"schemaVersion": 1, "shards": {"core": ["shell:pass.sh"]}},
        "core",
        root / "target" / "quality" / "shards" / "core",
    )

    assert receipt["runner"]["image"] == "ubuntu24@20260801.1"
    assert receipt["runner"]["os"] == "Linux"
    assert receipt["runner"]["python"]
    assert receipt["runner"]["cpuCount"] >= 1
    assert receipt["cache"] == {"status": "not_configured"}


def test_build_manifest_preserves_collected_nodes_and_non_pytest_project_test_commands():
    manifest = quality_test_manifest.build_manifest(
        ["tests/test_core.py::test_fast", "tests/test_installer.py::test_install"],
        {"tests/test_core.py::test_fast": 25},
    )

    assert [entry["id"] for entry in manifest["entries"]] == [
        "tests/test_core.py::test_fast",
        "tests/test_installer.py::test_install",
        "shell:tests/test_installer_boundaries.sh",
        "python:scripts/check_critical_coverage.py",
        "shell:tests/test_ci_release_evidence.sh",
    ]
    assert manifest["entries"][0]["durationMs"] == 25
    assert manifest["entries"][1]["durationMs"] == quality_test_manifest.DEFAULT_DURATION_MS
    assert manifest["nodeIds"] == [
        "tests/test_core.py::test_fast",
        "tests/test_installer.py::test_install",
    ]


def test_build_manifest_rejects_duplicate_or_non_node_collection_values():
    with pytest.raises(quality_test_manifest.ManifestError, match="duplicate"):
        quality_test_manifest.build_manifest(
            ["tests/test_core.py::test_a", "tests/test_core.py::test_a"], {}
        )
    with pytest.raises(quality_test_manifest.ManifestError, match="pytest node"):
        quality_test_manifest.build_manifest(["2287 tests collected"], {})


def test_historical_durations_reads_junit_node_times_and_ignores_invalid_cases(tmp_path):
    junit = tmp_path / "project-test.xml"
    junit.write_text(
        "<testsuite><testcase classname='tests.test_core' name='test_fast' time='0.025' />"
        "<testcase classname='tests.test_core' name='bad' time='not-a-number' /></testsuite>",
        encoding="utf-8",
    )

    assert quality_test_manifest.historical_durations(Path(junit)) == {
        "tests/test_core.py::test_fast": 25
    }


def test_timing_baseline_and_junit_parsing_fail_closed_on_malformed_evidence(tmp_path):
    malformed_junit = tmp_path / "malformed.xml"
    malformed_junit.write_text("<testsuite>", encoding="utf-8")
    assert quality_test_manifest.historical_durations(malformed_junit) == {}
    assert quality_test_manifest.historical_durations(tmp_path / "missing.xml") == {}

    invalid_schema = tmp_path / "invalid-schema.json"
    invalid_schema.write_text('{"schemaVersion": 2}', encoding="utf-8")
    with pytest.raises(quality_test_manifest.ManifestError, match="invalid timing baseline schema"):
        quality_test_manifest.load_file_timing_baseline(invalid_schema)

    invalid_entry = tmp_path / "invalid-entry.json"
    invalid_entry.write_text(
        '{"schemaVersion": 1, "fileDurationsMs": {"outside.py": 1}}', encoding="utf-8"
    )
    with pytest.raises(quality_test_manifest.ManifestError, match="invalid timing baseline entry"):
        quality_test_manifest.load_file_timing_baseline(invalid_entry)


def test_versioned_file_timing_baseline_balances_current_nodes_without_runner_junit(tmp_path):
    """Regression: Hosted plans must retain historical cost without target/ state."""
    baseline = tmp_path / "timing-baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "fileDurationsMs": {"tests/test_core.py": 100, "tests/test_slow.py": 300},
            }
        ),
        encoding="utf-8",
    )

    durations = quality_test_manifest.load_file_timing_baseline(baseline)
    manifest = quality_test_manifest.build_manifest(
        [
            "tests/test_core.py::test_one",
            "tests/test_core.py::test_two",
            "tests/test_slow.py::test_only",
            "tests/test_new.py::test_unseen",
        ],
        {},
        durations,
    )

    weights = {entry["id"]: entry["durationMs"] for entry in manifest["entries"]}
    assert weights["tests/test_core.py::test_one"] == 50
    assert weights["tests/test_core.py::test_two"] == 50
    assert weights["tests/test_slow.py::test_only"] == 300
    assert weights["tests/test_new.py::test_unseen"] == quality_test_manifest.DEFAULT_DURATION_MS


def test_manifest_cli_writes_live_collection_and_historical_weights(tmp_path, monkeypatch):
    output = tmp_path / "manifest.json"
    plan_output = tmp_path / "plan.json"
    baseline = tmp_path / "timing-baseline.json"
    baseline.write_text('{"schemaVersion": 1, "fileDurationsMs": {}}', encoding="utf-8")
    monkeypatch.setattr(
        quality_test_manifest,
        "collect_node_ids",
        lambda _root: ["tests/test_core.py::test_fast"],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "quality_test_manifest.py",
            "--root",
            str(tmp_path),
            "--junit",
            str(tmp_path / "missing.xml"),
            "--timing-baseline",
            str(baseline),
            "--output",
            str(output),
            "--plan-output",
            str(plan_output),
        ],
    )

    assert quality_test_manifest.main() == 0
    assert json.loads(output.read_text(encoding="utf-8"))["nodeIds"] == [
        "tests/test_core.py::test_fast"
    ]
    assert set(json.loads(plan_output.read_text(encoding="utf-8"))["shards"]) == set(
        quality_test_manifest.HOSTED_SHARDS
    )


def test_build_shard_plan_balances_complete_manifest_across_named_hosted_shards():
    manifest = {
        "schemaVersion": 1,
        "entries": [_entry("slow", 100), _entry("medium", 60), _entry("fast", 20)],
    }

    plan = quality_test_manifest.build_shard_plan(manifest, ["core", "governance"])

    assert plan["shards"] == {"core": ["slow"], "governance": ["medium", "fast"]}
    assert plan["loadsMs"] == {"core": 100, "governance": 80}
    assert plan["entryCount"] == 3


def test_build_shard_plan_keeps_full_coverage_check_in_aggregate_only_phase():
    """Regression: a partial shard must never enforce the full coverage gate."""
    manifest = quality_test_manifest.build_manifest(
        ["tests/test_core.py::test_fast", "tests/test_installer.py::test_install"], {}
    )

    plan = quality_test_manifest.build_shard_plan(manifest, ["core", "installer"])

    assigned = {entry for entries in plan["shards"].values() for entry in entries}
    assert "python:scripts/check_critical_coverage.py" not in assigned
    assert plan["aggregateEntries"] == ["python:scripts/check_critical_coverage.py"]
    assert assigned.union(plan["aggregateEntries"]) == {
        entry["id"] for entry in manifest["entries"]
    }


def test_manifest_plan_rejects_invalid_stages_and_unowned_nonlist_assignments():
    with pytest.raises(quality_test_manifest.ManifestError, match="unknown manifest stages"):
        quality_test_manifest.build_shard_plan(
            {"entries": [{"id": "bad", "durationMs": 1, "stage": "unowned"}]}, ["core"]
        )
    with pytest.raises(quality_test_manifest.ManifestError, match="entries must be a list"):
        quality_test_manifest.validate_assignments([_entry("a", 1)], {"core": "a"})  # type: ignore[arg-type]


def test_receipt_artifact_paths_reject_escapes_and_failed_shards():
    root = Path("/tmp/quality-test-manifest-root")
    receipt = _receipt("core", artifactRoot="target/quality/shards/core")
    assert quality_test_manifest.artifact_path(root, receipt, "junit") == (
        root / "target/quality/shards/core/core.xml"
    )

    for mutation in (
        {"artifactRoot": "/tmp/escape"},
        {"artifactRoot": "../escape"},
        {"artifacts": {**receipt["artifacts"], "junit": "../escape.xml"}},
        {"artifacts": {**receipt["artifacts"], "junit": "/tmp/escape.xml"}},
    ):
        broken = {**receipt, **mutation}
        with pytest.raises(quality_test_manifest.ManifestError, match="artifact"):
            quality_test_manifest.artifact_path(root, broken, "junit")

    with pytest.raises(quality_test_manifest.ManifestError, match="result is not passed"):
        quality_test_manifest.validate_aggregate(
            [_receipt("core", result="cancelled")],
            ["core"],
            {"commitSha": "a" * 40, "treeDigest": "sha256:" + "b" * 64},
        )


def test_run_shard_writes_source_bound_evidence_for_its_selected_test(tmp_path):
    """Regression: an executed shard must leave complete inspectable evidence."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests" / "test_piece.py").write_text(
        "def test_piece():\n    assert 2 + 2 == 4\n", encoding="utf-8"
    )
    (tmp_path / "scripts" / "piece.py").write_text("VALUE = 4\n", encoding="utf-8")
    for command in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "tests@example.invalid"],
        ["git", "config", "user.name", "Tests"],
        ["git", "add", "."],
        ["git", "commit", "-qm", "fixture"],
    ):
        subprocess.run(command, cwd=tmp_path, check=True)
    manifest = {
        "entries": [
            {
                "id": "tests/test_piece.py::test_piece",
                "durationMs": 1,
                "kind": "pytest",
                "stage": "shard",
            }
        ]
    }
    plan = {"shards": {"core": ["tests/test_piece.py::test_piece"]}}
    output = tmp_path / "evidence"

    receipt = quality_test_manifest.run_shard(tmp_path, manifest, plan, "core", output)

    assert receipt["result"] == "passed"
    assert receipt["artifactRoot"] == "evidence"
    assert len(receipt["manifestDigest"]) == 64
    assert len(receipt["planDigest"]) == 64
    assert len(receipt["commitSha"]) == 40
    assert receipt["treeDigest"].startswith("sha256:")
    for artifact in ("junit", "coverage", "coverageData", "timing", "gateLog", "receipt"):
        assert (tmp_path / receipt["artifactRoot"] / receipt["artifacts"][artifact]).is_file()


def test_run_aggregate_combines_every_successful_shard_coverage(tmp_path):
    """Regression: aggregate must combine raw data, not trust standalone coverage JSON."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text(
        "from scripts.piece import VALUE\n\ndef test_a():\n    assert VALUE == 4\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_b.py").write_text(
        "from scripts.piece import VALUE\n\ndef test_b():\n    assert VALUE == 4\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts" / "piece.py").write_text("VALUE = 4\n", encoding="utf-8")
    for command in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "tests@example.invalid"],
        ["git", "config", "user.name", "Tests"],
        ["git", "add", "."],
        ["git", "commit", "-qm", "fixture"],
    ):
        subprocess.run(command, cwd=tmp_path, check=True)
    manifest = {
        "entries": [
            {"id": "tests/test_a.py::test_a", "durationMs": 1, "kind": "pytest", "stage": "shard"},
            {"id": "tests/test_b.py::test_b", "durationMs": 1, "kind": "pytest", "stage": "shard"},
        ]
    }
    plan = {
        "shards": {
            "core": ["tests/test_a.py::test_a"],
            "governance": ["tests/test_b.py::test_b"],
        },
        "aggregateEntries": [],
    }
    receipts = [
        quality_test_manifest.run_shard(tmp_path, manifest, plan, "core", tmp_path / "core"),
        quality_test_manifest.run_shard(
            tmp_path, manifest, plan, "governance", tmp_path / "governance"
        ),
    ]

    receipt = quality_test_manifest.run_aggregate(
        tmp_path, manifest, plan, receipts, tmp_path / "aggregate"
    )

    assert receipt["result"] == "passed"
    assert (tmp_path / receipt["artifactRoot"] / receipt["artifacts"]["coverage"]).is_file()
    assert (tmp_path / receipt["artifactRoot"] / receipt["artifacts"]["receipt"]).is_file()
    assert all(
        (tmp_path / item["artifactRoot"] / item["artifacts"]["coverageData"]).is_file()
        for item in receipts
    )
    assert (
        quality_test_manifest.validate_aggregate_receipt(tmp_path, manifest, plan, receipt) is None
    )

    receipts[0]["planDigest"] = "0" * 64
    with pytest.raises(quality_test_manifest.ManifestError, match="planDigest"):
        quality_test_manifest.run_aggregate(
            tmp_path, manifest, plan, receipts, tmp_path / "mismatched-plan"
        )
