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
