import json

import pytest

from scripts import quality_measurements


def _sample(run_id: str, seconds: float, **overrides: object) -> dict[str, object]:
    sample: dict[str, object] = {
        "sampleKind": "candidate",
        "commitSha": "a" * 40,
        "treeDigest": "sha256:" + "b" * 64,
        "runner": {"image": "ubuntu-24.04", "os": "Linux", "python": "3.12.3"},
        "workflow": {"name": "smoke.yml", "runId": run_id, "attempt": 1},
        "result": "passed",
        "wallTimeSeconds": seconds,
    }
    sample.update(overrides)
    return sample


def test_validate_samples_returns_identity_and_nearest_rank_percentiles():
    report = quality_measurements.validate_samples(
        [_sample(str(index), value) for index, value in enumerate((400, 410, 420, 430, 440), 1)],
        expected_kind="candidate",
    )

    assert report["sampleCount"] == 5
    assert report["identity"]["commitSha"] == "a" * 40
    assert report["p50Seconds"] == 420
    assert report["p95Seconds"] == 440


def test_validate_samples_rejects_wrong_sha_and_non_successful_result():
    with pytest.raises(quality_measurements.MeasurementError, match="commitSha"):
        quality_measurements.validate_samples(
            [
                _sample(str(index), 400 + index, commitSha="c" * 40 if index == 5 else "a" * 40)
                for index in range(1, 6)
            ],
            expected_kind="candidate",
        )

    with pytest.raises(quality_measurements.MeasurementError, match="result"):
        quality_measurements.validate_samples(
            [
                _sample(str(index), 400 + index, result="cancelled" if index == 5 else "passed")
                for index in range(1, 6)
            ],
            expected_kind="candidate",
        )


def test_validate_samples_rejects_mixed_kind_duplicate_run_and_too_few_samples():
    with pytest.raises(quality_measurements.MeasurementError, match="sampleKind"):
        quality_measurements.validate_samples(
            [
                _sample(
                    str(index), 400 + index, sampleKind="baseline" if index == 5 else "candidate"
                )
                for index in range(1, 6)
            ],
            expected_kind="candidate",
        )

    with pytest.raises(quality_measurements.MeasurementError, match="duplicate workflow run"):
        quality_measurements.validate_samples(
            [
                _sample("same" if index in {4, 5} else str(index), 400 + index)
                for index in range(1, 6)
            ],
            expected_kind="candidate",
        )

    with pytest.raises(quality_measurements.MeasurementError, match="at least 5"):
        quality_measurements.validate_samples(
            [_sample(str(index), 400 + index) for index in range(1, 5)], expected_kind="candidate"
        )


def test_validate_samples_rejects_invalid_attempt_and_wall_time():
    with pytest.raises(quality_measurements.MeasurementError, match="workflow.attempt"):
        quality_measurements.validate_samples(
            [
                _sample(
                    str(index),
                    400 + index,
                    workflow={
                        "name": "smoke.yml",
                        "runId": str(index),
                        "attempt": 0 if index == 5 else 1,
                    },
                )
                for index in range(1, 6)
            ],
            expected_kind="candidate",
        )

    with pytest.raises(quality_measurements.MeasurementError, match="wallTimeSeconds"):
        quality_measurements.validate_samples(
            [_sample(str(index), True if index == 5 else 400 + index) for index in range(1, 6)],
            expected_kind="candidate",
        )


def test_build_hosted_receipt_binds_complete_project_test_evidence(tmp_path):
    aggregate = tmp_path / "aggregate"
    shards = tmp_path / "shards"
    aggregate.mkdir()
    manifest = {
        "schemaVersion": 1,
        "nodeIds": ["tests/test_one.py::test_pass", "tests/test_two.py::test_xfail"],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (aggregate / "receipt.json").write_text(
        json.dumps(
            {
                "commitSha": "a" * 40,
                "treeDigest": "sha256:" + "b" * 64,
                "result": "passed",
            }
        ),
        encoding="utf-8",
    )
    (aggregate / "coverage.json").write_text(
        json.dumps(
            {
                "meta": {"version": "7.10"},
                "files": {"scripts/one.py": {}},
                "totals": {"percent_covered": 85.2},
            }
        ),
        encoding="utf-8",
    )
    (aggregate / "gate.log").write_text("passed\n", encoding="utf-8")
    (aggregate / "timing.json").write_text("{}\n", encoding="utf-8")
    (aggregate / ".coverage").write_bytes(b"coverage-data")
    for shard, seconds in (("core", 10.0), ("installer", 20.0)):
        folder = shards / shard
        folder.mkdir(parents=True)
        (folder / "receipt.json").write_text(
            json.dumps(
                {
                    "shard": shard,
                    "commitSha": "a" * 40,
                    "treeDigest": "sha256:" + "b" * 64,
                    "result": "passed",
                    "runner": {
                        "image": "ubuntu24@20260801.1",
                        "os": "Linux",
                        "python": "3.12.3",
                        "cpuCount": 4,
                    },
                    "cache": {"status": "not_configured"},
                }
            ),
            encoding="utf-8",
        )
        (folder / "timing.json").write_text(
            json.dumps(
                {
                    "startedAt": f"2026-08-11T00:00:{10 if shard == 'core' else 12:02d}+00:00",
                    "finishedAt": f"2026-08-11T00:00:{20 if shard == 'core' else 32:02d}+00:00",
                    "wallTimeSeconds": seconds,
                    "topSlowTests": [[f"tests/{shard}.py::test_slow", int(seconds * 1000)]],
                }
            ),
            encoding="utf-8",
        )
        (folder / "junit.xml").write_text(
            (
                '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="'
                + ("1" if shard == "installer" else "0")
                + '"><testcase classname="tests.test" name="case">'
                + ('<skipped type="pytest.xfail">known</skipped>' if shard == "installer" else "")
                + "</testcase></testsuite></testsuites>"
            ),
            encoding="utf-8",
        )
        (folder / "coverage.json").write_text("{}\n", encoding="utf-8")
        (folder / "gate.log").write_text("passed\n", encoding="utf-8")
        (folder / ".coverage").write_bytes(b"coverage-data")
    provider_run = {
        "id": 123,
        "run_attempt": 1,
        "created_at": "2026-08-11T00:00:00Z",
        "html_url": "https://example.invalid/actions/runs/123",
        "head_sha": "a" * 40,
        "status": "in_progress",
        "conclusion": None,
    }
    provider_jobs = {
        "jobs": [
            {
                "name": "project-test-manifest",
                "started_at": "2026-08-11T00:00:05Z",
                "completed_at": "2026-08-11T00:00:10Z",
                "conclusion": "success",
            },
            {
                "name": "project-test-core",
                "started_at": "2026-08-11T00:00:10Z",
                "completed_at": "2026-08-11T00:00:20Z",
                "conclusion": "success",
            },
            {
                "name": "project-test-installer",
                "started_at": "2026-08-11T00:00:12Z",
                "completed_at": "2026-08-11T00:00:32Z",
                "conclusion": "success",
            },
            {
                "name": "template-smoke",
                "started_at": "2026-08-11T00:00:32Z",
                "completed_at": "2026-08-11T00:00:40Z",
                "conclusion": "success",
            },
        ]
    }

    receipt = quality_measurements.build_hosted_receipt(
        aggregate_root=aggregate,
        shards_root=shards,
        manifest_path=tmp_path / "manifest.json",
        provider_run=provider_run,
        provider_jobs=provider_jobs,
        repository="owner/repository",
        ref="refs/heads/work",
    )

    assert receipt["commitSha"] == "a" * 40
    assert receipt["treeDigest"].startswith("sha256:")
    assert receipt["runner"]["cpuCount"] == 4
    assert receipt["workflow"]["runId"] == "123"
    assert receipt["workflow"]["providerStatusAtReceipt"] == "in_progress"
    assert receipt["gates"]["project-test"]["wallTimeSeconds"] == 27.0
    assert receipt["gates"]["template-smoke"]["wallTimeSeconds"] == 40.0
    assert receipt["tests"] == {
        "collected": 2,
        "passed": 1,
        "failed": 0,
        "errors": 0,
        "skipped": 1,
        "xfail": 1,
        "nodeIdDigest": quality_measurements.sha256_json(manifest["nodeIds"]),
    }
    assert receipt["coverage"]["percent"] == 85.2
    assert receipt["coverage"]["sourceDigest"].startswith("sha256:")
    assert receipt["topSlowTests"][0][0] == "tests/installer.py::test_slow"
    assert receipt["artifacts"]["aggregate/coverage.json"].startswith("sha256:")


def test_build_hosted_receipt_fails_closed_on_wrong_shard_sha(tmp_path):
    aggregate = tmp_path / "aggregate"
    shard = tmp_path / "shards" / "core"
    aggregate.mkdir(parents=True)
    shard.mkdir(parents=True)
    (aggregate / "receipt.json").write_text(
        json.dumps({"commitSha": "a" * 40, "treeDigest": "sha256:" + "b" * 64}),
        encoding="utf-8",
    )
    (shard / "receipt.json").write_text(
        json.dumps({"commitSha": "c" * 40, "treeDigest": "sha256:" + "b" * 64}),
        encoding="utf-8",
    )

    with pytest.raises(quality_measurements.MeasurementError, match="commitSha"):
        quality_measurements.build_hosted_receipt(
            aggregate_root=aggregate,
            shards_root=tmp_path / "shards",
            manifest_path=tmp_path / "missing.json",
            provider_run={},
            provider_jobs={},
            repository="owner/repository",
            ref="refs/heads/work",
        )
