"""Validate comparable Hosted-quality samples and calculate conservative percentiles."""

from __future__ import annotations

import math
from typing import Any


class MeasurementError(ValueError):
    """Raised when a performance sample cannot safely enter a comparison."""


IDENTITY_FIELDS = ("commitSha", "treeDigest")
RUNNER_FIELDS = ("image", "os", "python")


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MeasurementError(f"{name} must be an object")
    return value


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MeasurementError(f"{name} must be a non-empty string")
    return value


def _identity(sample: dict[str, Any]) -> dict[str, str]:
    runner = _mapping(sample.get("runner"), "runner")
    return {
        **{field: _text(sample.get(field), field) for field in IDENTITY_FIELDS},
        **{
            f"runner.{field}": _text(runner.get(field), f"runner.{field}")
            for field in RUNNER_FIELDS
        },
    }


def _nearest_rank(values: list[float], percentile: int) -> float:
    index = max(0, math.ceil(percentile / 100 * len(values)) - 1)
    return values[index]


def validate_samples(samples: list[dict[str, Any]], *, expected_kind: str) -> dict[str, Any]:
    """Return a source-bound p50/p95 report or reject incomparable evidence.

    A successful comparison needs five sequential, unique workflow run/attempt
    samples of one declared kind.  This function intentionally rejects a
    cancelled or otherwise non-successful sample instead of filtering it out.
    """
    if len(samples) < 5:
        raise MeasurementError("at least 5 comparable samples are required")
    expected_identity: dict[str, str] | None = None
    seen_runs: set[tuple[str, int]] = set()
    values: list[float] = []
    for index, raw_sample in enumerate(samples, 1):
        sample = _mapping(raw_sample, f"sample {index}")
        if sample.get("sampleKind") != expected_kind:
            raise MeasurementError("sampleKind does not match expected comparison set")
        if sample.get("result") != "passed":
            raise MeasurementError("result must be passed for every comparable sample")
        identity = _identity(sample)
        if expected_identity is None:
            expected_identity = identity
        else:
            for key, value in identity.items():
                if expected_identity[key] != value:
                    raise MeasurementError(f"{key} differs between comparable samples")
        workflow = _mapping(sample.get("workflow"), "workflow")
        run_id = _text(workflow.get("runId"), "workflow.runId")
        attempt = workflow.get("attempt")
        if not isinstance(attempt, int) or attempt < 1:
            raise MeasurementError("workflow.attempt must be a positive integer")
        run_key = (run_id, attempt)
        if run_key in seen_runs:
            raise MeasurementError("duplicate workflow run/attempt is not a distinct sample")
        seen_runs.add(run_key)
        wall_time = sample.get("wallTimeSeconds")
        if not isinstance(wall_time, (int, float)) or isinstance(wall_time, bool) or wall_time < 0:
            raise MeasurementError("wallTimeSeconds must be a non-negative number")
        values.append(float(wall_time))
    ordered = sorted(values)
    if expected_identity is None:
        raise MeasurementError("comparable samples are required")
    return {
        "schemaVersion": 1,
        "sampleKind": expected_kind,
        "sampleCount": len(samples),
        "identity": {
            "commitSha": expected_identity["commitSha"],
            "treeDigest": expected_identity["treeDigest"],
            "runner": {field: expected_identity[f"runner.{field}"] for field in RUNNER_FIELDS},
        },
        "p50Seconds": _nearest_rank(ordered, 50),
        "p95Seconds": _nearest_rank(ordered, 95),
        "samples": samples,
    }
