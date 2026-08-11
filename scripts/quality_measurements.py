"""Validate comparable Hosted-quality samples and calculate conservative percentiles."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree  # nosec B405 - reads generated JUnit only.


class MeasurementError(ValueError):
    """Raised when a performance sample cannot safely enter a comparison."""


IDENTITY_FIELDS = ("commitSha", "treeDigest")
RUNNER_FIELDS = ("image", "os", "python")


def sha256_json(value: Any) -> str:
    """Return a canonical JSON digest with an explicit algorithm prefix."""
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path, name: str) -> dict[str, Any]:
    if not path.is_file():
        raise MeasurementError(f"{name} is missing")
    try:
        return _mapping(json.loads(path.read_text(encoding="utf-8")), name)
    except (OSError, json.JSONDecodeError) as error:
        raise MeasurementError(f"{name} is invalid: {error}") from error


def _timestamp(value: Any, name: str) -> datetime:
    text = _text(value, name).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError as error:
        raise MeasurementError(f"{name} is not an ISO timestamp") from error


def _job_map(provider_jobs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    jobs = provider_jobs.get("jobs")
    if not isinstance(jobs, list):
        raise MeasurementError("provider jobs must contain a jobs list")
    result: dict[str, dict[str, Any]] = {}
    for raw in jobs:
        job = _mapping(raw, "provider job")
        name = _text(job.get("name"), "provider job name")
        if name in result:
            raise MeasurementError(f"duplicate provider job: {name}")
        result[name] = job
    return result


def _gate(job: dict[str, Any], name: str) -> tuple[datetime, datetime]:
    if job.get("conclusion") != "success":
        raise MeasurementError(f"provider job {name} did not succeed")
    return (
        _timestamp(job.get("started_at"), f"{name}.started_at"),
        _timestamp(job.get("completed_at"), f"{name}.completed_at"),
    )


def _junit_counts(path: Path) -> dict[str, int]:
    if not path.is_file():
        raise MeasurementError(f"JUnit artifact is missing: {path}")
    try:
        root = ElementTree.parse(path).getroot()  # nosec B314 - local generated evidence.
    except (OSError, ElementTree.ParseError) as error:
        raise MeasurementError(f"JUnit artifact is invalid: {path}: {error}") from error
    cases = list(root.iter("testcase"))
    failures = sum(1 for case in cases if case.find("failure") is not None)
    errors = sum(1 for case in cases if case.find("error") is not None)
    skipped = 0
    xfail = 0
    for case in cases:
        node = case.find("skipped")
        if node is None:
            continue
        skipped += 1
        if (
            "xfail" in str(node.attrib.get("type", "")).lower()
            or "xfail" in str(node.attrib.get("message", "")).lower()
        ):
            xfail += 1
    return {
        "tests": len(cases),
        "passed": len(cases) - failures - errors - skipped,
        "failed": failures,
        "errors": errors,
        "skipped": skipped,
        "xfail": xfail,
    }


def build_hosted_receipt(
    *,
    aggregate_root: Path,
    shards_root: Path,
    manifest_path: Path,
    provider_run: dict[str, Any],
    provider_jobs: dict[str, Any],
    repository: str,
    ref: str,
) -> dict[str, Any]:
    """Build a fail-closed, source-bound Hosted measurement receipt."""
    aggregate = _load_json(aggregate_root / "receipt.json", "aggregate receipt")
    commit_sha = _text(aggregate.get("commitSha"), "aggregate commitSha")
    tree_digest = _text(aggregate.get("treeDigest"), "aggregate treeDigest")
    shard_folders = sorted(path for path in shards_root.iterdir() if path.is_dir())
    if not shard_folders:
        raise MeasurementError("at least one shard artifact directory is required")

    receipts: list[tuple[Path, dict[str, Any]]] = []
    runner: dict[str, Any] | None = None
    cache: dict[str, Any] = {}
    for folder in shard_folders:
        receipt = _load_json(folder / "receipt.json", f"{folder.name} receipt")
        for field, expected in (("commitSha", commit_sha), ("treeDigest", tree_digest)):
            if receipt.get(field) != expected:
                raise MeasurementError(f"shard {folder.name} {field} differs from aggregate")
        if receipt.get("result") != "passed":
            raise MeasurementError(f"shard {folder.name} result must be passed")
        current_runner = _mapping(receipt.get("runner"), f"shard {folder.name} runner")
        for field in (*RUNNER_FIELDS, "cpuCount"):
            if field not in current_runner:
                raise MeasurementError(f"shard {folder.name} runner.{field} is missing")
        if runner is None:
            runner = current_runner
        elif runner != current_runner:
            raise MeasurementError(f"shard {folder.name} runner differs from other shards")
        cache[folder.name] = _mapping(receipt.get("cache"), f"shard {folder.name} cache")
        receipts.append((folder, receipt))

    manifest = _load_json(manifest_path, "project-test manifest")
    node_ids = manifest.get("nodeIds")
    if not isinstance(node_ids, list) or not all(isinstance(node, str) for node in node_ids):
        raise MeasurementError("project-test manifest nodeIds must be a string list")
    coverage = _load_json(aggregate_root / "coverage.json", "aggregate coverage")
    totals = _mapping(coverage.get("totals"), "aggregate coverage totals")
    percent = totals.get("percent_covered")
    if not isinstance(percent, (int, float)) or isinstance(percent, bool):
        raise MeasurementError("aggregate coverage percent_covered must be numeric")
    sources = sorted(coverage.get("files", {}))
    if not sources:
        raise MeasurementError("aggregate coverage source set is empty")

    counts = {key: 0 for key in ("tests", "passed", "failed", "errors", "skipped", "xfail")}
    slow: list[list[Any]] = []
    artifacts: dict[str, str] = {}
    required_shard_files = (
        "receipt.json",
        "timing.json",
        "junit.xml",
        "coverage.json",
        "gate.log",
        ".coverage",
    )
    for folder, _receipt in receipts:
        for key, value in _junit_counts(folder / "junit.xml").items():
            counts[key] += value
        timing = _load_json(folder / "timing.json", f"{folder.name} timing")
        entries = timing.get("topSlowTests")
        if not isinstance(entries, list):
            raise MeasurementError(f"{folder.name} timing topSlowTests must be a list")
        slow.extend(entries)
        for filename in required_shard_files:
            path = folder / filename
            if not path.is_file():
                raise MeasurementError(f"shard artifact is missing: {folder.name}/{filename}")
            artifacts[f"shards/{folder.name}/{filename}"] = _sha256_file(path)
    if counts["tests"] != len(node_ids):
        raise MeasurementError("JUnit test count differs from manifest node ID count")
    if counts["failed"] or counts["errors"]:
        raise MeasurementError("successful measurement contains failed or errored tests")
    required_aggregate_files = (
        "receipt.json",
        "timing.json",
        "coverage.json",
        "gate.log",
        ".coverage",
    )
    for filename in required_aggregate_files:
        path = aggregate_root / filename
        if not path.is_file():
            raise MeasurementError(f"aggregate artifact is missing: {filename}")
        artifacts[f"aggregate/{filename}"] = _sha256_file(path)

    run_sha = _text(provider_run.get("head_sha"), "provider run head_sha")
    if run_sha != commit_sha:
        raise MeasurementError("provider run head_sha differs from aggregate commitSha")
    provider_conclusion = provider_run.get("conclusion")
    if provider_conclusion not in {None, "", "success"}:
        raise MeasurementError("provider run conclusion is already non-successful")
    jobs = _job_map(provider_jobs)
    manifest_started, _ = _gate(jobs["project-test-manifest"], "project-test-manifest")
    shard_job_names = [f"project-test-{folder.name}" for folder, _ in receipts]
    shard_ends = [_gate(jobs[name], name)[1] for name in shard_job_names]
    template_started, template_finished = _gate(jobs["template-smoke"], "template-smoke")
    run_created = _timestamp(provider_run.get("created_at"), "provider run created_at")

    run_id = provider_run.get("id")
    attempt = provider_run.get("run_attempt")
    if not isinstance(run_id, int) or not isinstance(attempt, int) or attempt < 1:
        raise MeasurementError("provider run id/attempt must be positive integers")
    if runner is None:
        raise MeasurementError("runner facts are missing")
    return {
        "format": "ai-cockpit-hosted-measurement-receipt",
        "schemaVersion": 2,
        "purpose": "hosted_measurement",
        "authorizationClaim": "not_provided_by_receipt",
        "forbiddenActions": [
            "pull_request",
            "merge",
            "release",
            "archive_mutation",
            "work_item_closure",
            "branch_deletion",
        ],
        "repository": repository,
        "ref": ref,
        "commitSha": commit_sha,
        "treeDigest": tree_digest,
        "runner": runner,
        "cache": cache,
        "workflow": {
            "name": "smoke.yml",
            "runId": str(run_id),
            "attempt": attempt,
            "url": _text(provider_run.get("html_url"), "provider run html_url"),
            "providerStatusAtReceipt": _text(provider_run.get("status"), "provider run status"),
            "providerConclusionAtReceipt": provider_conclusion,
        },
        "result": "passed",
        "gates": {
            "project-test": {
                "startedAt": manifest_started.isoformat(),
                "finishedAt": max(shard_ends).isoformat(),
                "wallTimeSeconds": (max(shard_ends) - manifest_started).total_seconds(),
            },
            "template-smoke": {
                "startedAt": run_created.isoformat(),
                "jobStartedAt": template_started.isoformat(),
                "finishedAt": template_finished.isoformat(),
                "wallTimeSeconds": (template_finished - run_created).total_seconds(),
            },
        },
        "tests": {
            "collected": len(node_ids),
            "passed": counts["passed"],
            "failed": counts["failed"],
            "errors": counts["errors"],
            "skipped": counts["skipped"],
            "xfail": counts["xfail"],
            "nodeIdDigest": sha256_json(node_ids),
        },
        "coverage": {
            "percent": float(percent),
            "sourceCount": len(sources),
            "sourceDigest": sha256_json(sources),
        },
        "topSlowTests": sorted(slow, key=lambda item: -float(item[1]))[:25],
        "artifacts": artifacts,
    }


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build-receipt")
    build.add_argument("--aggregate-root", type=Path, required=True)
    build.add_argument("--shards-root", type=Path, required=True)
    build.add_argument("--manifest", type=Path, required=True)
    build.add_argument("--provider-run", type=Path, required=True)
    build.add_argument("--provider-jobs", type=Path, required=True)
    build.add_argument("--repository", required=True)
    build.add_argument("--ref", required=True)
    build.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build-receipt":
        receipt = build_hosted_receipt(
            aggregate_root=args.aggregate_root,
            shards_root=args.shards_root,
            manifest_path=args.manifest,
            provider_run=_load_json(args.provider_run, "provider run"),
            provider_jobs=_load_json(args.provider_jobs, "provider jobs"),
            repository=args.repository,
            ref=args.ref,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    raise MeasurementError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
