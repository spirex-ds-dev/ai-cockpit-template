"""Deterministic test-shard ownership and fail-closed aggregate validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess  # nosec B404 - all invocations below use fixed executables and validated args.
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree  # nosec B405 - reads only local pytest-generated JUnit evidence.


class ManifestError(ValueError):
    """Raised when a test manifest or shard aggregate is incomplete."""


REQUIRED_ARTIFACTS = ("junit", "coverage", "coverageData", "timing", "gateLog", "receipt")
REQUIRED_SOURCE_FIELDS = ("commitSha", "treeDigest")
DEFAULT_DURATION_MS = 1
PROJECT_TEST_COMMANDS = (
    ("shell:tests/test_installer_boundaries.sh", "shell", "shard"),
    ("python:scripts/check_critical_coverage.py", "python", "aggregate"),
    ("shell:tests/test_ci_release_evidence.sh", "shell", "shard"),
)
HOSTED_SHARDS = ("core", "governance", "installer", "lifecycle", "release")


def runner_facts() -> dict[str, Any]:
    """Return stable facts needed to compare Hosted runner populations."""
    image_os = os.environ.get("ImageOS", "local")
    image_version = os.environ.get("ImageVersion", "unversioned")
    return {
        "image": f"{image_os}@{image_version}",
        "os": os.environ.get("RUNNER_OS", platform.system()),
        "python": platform.python_version(),
        "cpuCount": os.cpu_count() or 1,
    }


def document_digest(document: dict[str, Any]) -> str:
    """Return a stable digest for a manifest or shard plan receipt binding."""
    return hashlib.sha256(
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def historical_durations(junit_path: Path) -> dict[str, int]:
    """Translate previous JUnit testcase timings into pytest node-ID weights."""
    if not junit_path.is_file():
        return {}
    try:
        root = ElementTree.parse(junit_path).getroot()  # nosec B314 - JUnit is generated locally by pytest.
    except ElementTree.ParseError:
        return {}
    durations: dict[str, int] = {}
    for case in root.findall(".//testcase"):
        classname, name, seconds = case.get("classname"), case.get("name"), case.get("time")
        if not classname or not name or not seconds:
            continue
        try:
            duration_ms = max(0, round(float(seconds) * 1000))
        except ValueError:
            continue
        node_id = f"{classname.replace('.', '/')}.py::{name}"
        durations[node_id] = duration_ms
    return durations


def load_file_timing_baseline(path: Path) -> dict[str, int]:
    """Load checked-in file and exact-node costs; reject malformed evidence."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"unable to load timing baseline {path}: {exc}") from exc
    if payload.get("schemaVersion") != 1 or not isinstance(payload.get("fileDurationsMs"), dict):
        raise ManifestError(f"invalid timing baseline schema: {path}")
    durations: dict[str, int] = {}
    for filename, duration in payload["fileDurationsMs"].items():
        if (
            not isinstance(filename, str)
            or not filename.startswith("tests/")
            or not filename.endswith(".py")
            or not isinstance(duration, int)
            or isinstance(duration, bool)
            or duration < 0
        ):
            raise ManifestError(f"invalid timing baseline entry: {filename}")
        durations[filename] = duration
    node_durations = payload.get("nodeDurationsMs", {})
    if not isinstance(node_durations, dict):
        raise ManifestError(f"invalid timing baseline nodeDurationsMs: {path}")
    for node_id, duration in node_durations.items():
        if (
            not isinstance(node_id, str)
            or not node_id.startswith("tests/")
            or ".py::" not in node_id
            or not isinstance(duration, int)
            or isinstance(duration, bool)
            or duration < 0
        ):
            raise ManifestError(f"invalid timing baseline node entry: {node_id}")
        durations[node_id] = duration
    return durations


def collect_node_ids(root: Path) -> list[str]:
    """Collect the current pytest node set without running the tests."""
    result = subprocess.run(  # nosec B603 - fixed Python executable and pytest collection arguments.
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ManifestError(f"pytest collection failed: {result.stderr.strip()}")
    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.startswith("tests/") and "::" in line
    ]


def source_identity(root: Path) -> dict[str, str]:
    """Return the commit and content-tree identity that binds shard evidence."""
    commit = subprocess.run(  # nosec B603 B607 - fixed git executable and argument list.
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False
    )
    tree = subprocess.run(  # nosec B603 B607 - fixed git executable and argument list.
        ["git", "ls-tree", "-r", "-z", "HEAD"],
        cwd=root,
        text=False,
        capture_output=True,
        check=False,
    )
    if commit.returncode != 0 or tree.returncode != 0:
        raise ManifestError("unable to establish source commit and tree digest")
    return {
        "commitSha": commit.stdout.strip(),
        "treeDigest": "sha256:" + hashlib.sha256(tree.stdout).hexdigest(),
    }


def artifact_root(root: Path, output: Path) -> str:
    """Bind evidence locations to the repository, never to a runner-specific absolute path."""
    try:
        return str(output.resolve().relative_to(root.resolve()))
    except ValueError as exc:
        raise ManifestError("artifact output must be inside the repository root") from exc


def artifact_path(root: Path, receipt: dict[str, Any], artifact: str) -> Path:
    """Resolve an artifact only through its receipt-bound repository-relative root."""
    relative_root = receipt.get("artifactRoot")
    artifacts = receipt.get("artifacts")
    if (
        not isinstance(relative_root, str)
        or not relative_root
        or Path(relative_root).is_absolute()
        or ".." in Path(relative_root).parts
    ):
        raise ManifestError(f"shard {receipt.get('shard', 'aggregate')} artifactRoot is invalid")
    if not isinstance(artifacts, dict) or not isinstance(artifacts.get(artifact), str):
        raise ManifestError(
            f"shard {receipt.get('shard', 'aggregate')} {artifact} artifact is invalid"
        )
    relative_name = Path(artifacts[artifact])
    if relative_name.is_absolute() or ".." in relative_name.parts:
        raise ManifestError(
            f"shard {receipt.get('shard', 'aggregate')} {artifact} artifact escapes root"
        )
    return root / relative_root / relative_name


def _write_failure_placeholders(output: Path, detail: str) -> None:
    """Preserve evidence paths even when a runner fails before pytest writes them."""
    junit = output / "junit.xml"
    if not junit.exists():
        junit.write_text(
            '<testsuite name="project-test-shard" errors="1"><testcase name="runner">'
            f"<error>{detail}</error></testcase></testsuite>\n",
            encoding="utf-8",
        )
    coverage = output / "coverage.json"
    if not coverage.exists():
        coverage.write_text("{}\n", encoding="utf-8")
    coverage_data = output / ".coverage"
    if not coverage_data.exists():
        coverage_data.touch()


def run_shard(
    root: Path, manifest: dict[str, Any], plan: dict[str, Any], shard: str, output: Path
) -> dict[str, Any]:
    """Run one isolated shard and write source-bound evidence on every outcome."""
    entries = {
        entry["id"]: entry for entry in manifest.get("entries", []) if isinstance(entry, dict)
    }
    shard_entries = plan.get("shards", {}).get(shard)
    if not isinstance(shard_entries, list) or not shard_entries:
        raise ManifestError(f"shard {shard} has no assigned entries")
    selected = []
    for identifier in shard_entries:
        entry = entries.get(identifier)
        if entry is None or entry.get("stage", "shard") != "shard":
            raise ManifestError(f"shard {shard} references invalid entry: {identifier}")
        selected.append(entry)
    output.mkdir(parents=True, exist_ok=True)
    identity = source_identity(root)
    junit = output / "junit.xml"
    coverage = output / "coverage.json"
    timing = output / "timing.json"
    gate_log = output / "gate.log"
    receipt_path = output / "receipt.json"
    started = datetime.now(UTC)
    result = "passed"
    recovery = "make project-test"
    environment = os.environ.copy()
    environment["COVERAGE_FILE"] = str(output / ".coverage")
    pytest_ids = [entry["id"] for entry in selected if entry.get("kind") == "pytest"]
    commands: list[list[str]] = []
    if pytest_ids:
        commands.append(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--cov=scripts",
                f"--cov-report=json:{coverage}",
                f"--junitxml={junit}",
                "--durations=25",
                "--durations-min=1",
                *pytest_ids,
            ]
        )
    for entry in selected:
        identifier = entry["id"]
        if entry.get("kind") == "shell" and identifier.startswith("shell:"):
            commands.append(["bash", identifier.removeprefix("shell:")])
        elif entry.get("kind") == "python" and identifier.startswith("python:"):
            commands.append([sys.executable, identifier.removeprefix("python:")])
    with gate_log.open("w", encoding="utf-8") as log:
        for command in commands:
            log.write("$ " + " ".join(command) + "\n")
            completed = subprocess.run(  # nosec B603 - commands derive from validated manifest entries only.
                command,
                cwd=root,
                text=True,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=environment,
                check=False,
            )
            if completed.returncode != 0:
                result = "failed"
                recovery = " ".join(command)
                break
    finished = datetime.now(UTC)
    _write_failure_placeholders(output, f"shard {shard} {result}; recovery: {recovery}")
    timing.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "shard": shard,
                "startedAt": started.isoformat(),
                "finishedAt": finished.isoformat(),
                "wallTimeSeconds": (finished - started).total_seconds(),
                "topSlowTests": sorted(
                    historical_durations(junit).items(), key=lambda item: -item[1]
                )[:25],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    receipt = {
        "schemaVersion": 1,
        "shard": shard,
        **identity,
        "manifestDigest": document_digest(manifest),
        "planDigest": document_digest(plan),
        "artifactRoot": artifact_root(root, output),
        "result": result,
        "recovery": recovery,
        "runner": runner_facts(),
        "cache": {"status": "not_configured"},
        "artifacts": {
            "junit": junit.name,
            "coverage": coverage.name,
            "coverageData": ".coverage",
            "timing": timing.name,
            "gateLog": gate_log.name,
            "receipt": receipt_path.name,
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def run_aggregate(
    root: Path,
    manifest: dict[str, Any],
    plan: dict[str, Any],
    receipts: list[dict[str, Any]],
    output: Path,
) -> dict[str, Any]:
    """Combine exactly the source-bound successful shard coverage artifacts."""
    output.mkdir(parents=True, exist_ok=True)
    identity = source_identity(root)
    shards = plan.get("shards")
    if not isinstance(shards, dict) or not shards:
        raise ManifestError("aggregate requires named shard assignments")
    expected_shards = list(shards)
    validate_aggregate(receipts, expected_shards, identity)
    expected_manifest_digest = document_digest(manifest)
    expected_plan_digest = document_digest(plan)
    for receipt in receipts:
        if receipt.get("manifestDigest") != expected_manifest_digest:
            raise ManifestError(f"shard {receipt['shard']} manifestDigest does not match aggregate")
        if receipt.get("planDigest") != expected_plan_digest:
            raise ManifestError(f"shard {receipt['shard']} planDigest does not match aggregate")
    coverage_inputs: list[str] = []
    for receipt in receipts:
        for artifact in REQUIRED_ARTIFACTS:
            path = artifact_path(root, receipt, artifact)
            if not path.is_file():
                raise ManifestError(
                    f"shard {receipt['shard']} {artifact} artifact is missing on disk"
                )
        coverage_inputs.append(str(artifact_path(root, receipt, "coverageData")))
    entries = {
        entry["id"]: entry for entry in manifest.get("entries", []) if isinstance(entry, dict)
    }
    aggregate_ids = plan.get("aggregateEntries", [])
    if not isinstance(aggregate_ids, list):
        raise ManifestError("aggregateEntries must be a list")
    aggregate_entries: list[dict[str, Any]] = []
    for identifier in aggregate_ids:
        entry = entries.get(identifier)
        if entry is None or entry.get("stage") != "aggregate":
            raise ManifestError(f"aggregate references invalid entry: {identifier}")
        aggregate_entries.append(entry)
    coverage = output / "coverage.json"
    coverage_data = output / ".coverage"
    timing = output / "timing.json"
    gate_log = output / "gate.log"
    receipt_path = output / "receipt.json"
    started = datetime.now(UTC)
    result = "passed"
    recovery = "make project-test"
    commands = [
        [sys.executable, "-m", "coverage", "combine", "--keep", *coverage_inputs],
        [sys.executable, "-m", "coverage", "json", "-o", str(coverage)],
        [sys.executable, "-m", "coverage", "report", "--fail-under=85.10"],
    ]
    for entry in aggregate_entries:
        identifier = entry["id"]
        if (
            entry.get("kind") == "python"
            and identifier == "python:scripts/check_critical_coverage.py"
        ):
            commands.append([sys.executable, "scripts/check_critical_coverage.py", str(coverage)])
        else:
            raise ManifestError(f"unsupported aggregate entry: {identifier}")
    environment = os.environ.copy()
    environment["COVERAGE_FILE"] = str(coverage_data)
    with gate_log.open("w", encoding="utf-8") as log:
        for command in commands:
            log.write("$ " + " ".join(command) + "\n")
            completed = subprocess.run(  # nosec B603 - aggregate command list is constructed internally.
                command,
                cwd=root,
                text=True,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=environment,
                check=False,
            )
            if completed.returncode != 0:
                result = "failed"
                recovery = " ".join(command)
                break
    finished = datetime.now(UTC)
    _write_failure_placeholders(output, f"aggregate {result}; recovery: {recovery}")
    timing.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "startedAt": started.isoformat(),
                "finishedAt": finished.isoformat(),
                "wallTimeSeconds": (finished - started).total_seconds(),
                "shards": expected_shards,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    receipt = {
        "schemaVersion": 1,
        "aggregate": "project-test",
        **identity,
        "manifestDigest": expected_manifest_digest,
        "planDigest": expected_plan_digest,
        "artifactRoot": artifact_root(root, output),
        "result": result,
        "recovery": recovery,
        "artifacts": {
            "coverage": coverage.name,
            "coverageData": ".coverage",
            "timing": timing.name,
            "gateLog": gate_log.name,
            "receipt": receipt_path.name,
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def validate_aggregate_receipt(
    root: Path, manifest: dict[str, Any], plan: dict[str, Any], receipt: dict[str, Any]
) -> None:
    """Validate a downloaded aggregate receipt before a downstream gate reuses it."""
    if receipt.get("aggregate") != "project-test" or receipt.get("result") != "passed":
        raise ManifestError("project-test aggregate receipt is not a successful aggregate")
    identity = source_identity(root)
    for field, expected in identity.items():
        if receipt.get(field) != expected:
            raise ManifestError(f"aggregate receipt {field} does not match current source")
    if receipt.get("manifestDigest") != document_digest(manifest):
        raise ManifestError("aggregate receipt manifestDigest does not match current manifest")
    if receipt.get("planDigest") != document_digest(plan):
        raise ManifestError("aggregate receipt planDigest does not match current plan")
    for artifact in ("coverage", "coverageData", "timing", "gateLog", "receipt"):
        if not artifact_path(root, receipt, artifact).is_file():
            raise ManifestError(f"aggregate receipt {artifact} artifact is missing on disk")


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "validate-aggregate-receipt":
        parser = argparse.ArgumentParser(
            description="Validate a reusable project-test aggregate receipt."
        )
        parser.add_argument("--root", type=Path, default=Path("."))
        parser.add_argument("--manifest", type=Path, required=True)
        parser.add_argument("--plan", type=Path, required=True)
        parser.add_argument("--receipt", type=Path, required=True)
        args = parser.parse_args(sys.argv[2:])
        root = args.root.resolve()
        validate_aggregate_receipt(
            root,
            json.loads(args.manifest.read_text(encoding="utf-8")),
            json.loads(args.plan.read_text(encoding="utf-8")),
            json.loads(args.receipt.read_text(encoding="utf-8")),
        )
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "run-shard":
        parser = argparse.ArgumentParser(description="Run one source-bound project-test shard.")
        parser.add_argument("--root", type=Path, default=Path("."))
        parser.add_argument("--manifest", type=Path, required=True)
        parser.add_argument("--plan", type=Path, required=True)
        parser.add_argument("--shard", required=True)
        parser.add_argument("--output", type=Path, required=True)
        args = parser.parse_args(sys.argv[2:])
        root = args.root.resolve()
        receipt = run_shard(
            root,
            json.loads(args.manifest.read_text(encoding="utf-8")),
            json.loads(args.plan.read_text(encoding="utf-8")),
            args.shard,
            args.output,
        )
        return 0 if receipt["result"] == "passed" else 1
    if len(sys.argv) > 1 and sys.argv[1] == "aggregate":
        parser = argparse.ArgumentParser(description="Aggregate source-bound project-test shards.")
        parser.add_argument("--root", type=Path, default=Path("."))
        parser.add_argument("--manifest", type=Path, required=True)
        parser.add_argument("--plan", type=Path, required=True)
        parser.add_argument("--receipt", type=Path, action="append", required=True)
        parser.add_argument("--output", type=Path, required=True)
        args = parser.parse_args(sys.argv[2:])
        root = args.root.resolve()
        receipt = run_aggregate(
            root,
            json.loads(args.manifest.read_text(encoding="utf-8")),
            json.loads(args.plan.read_text(encoding="utf-8")),
            [json.loads(path.read_text(encoding="utf-8")) for path in args.receipt],
            args.output,
        )
        return 0 if receipt["result"] == "passed" else 1
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--junit", type=Path, default=Path("target/quality/junit/project-test.xml"))
    parser.add_argument(
        "--timing-baseline",
        type=Path,
        default=Path("docs/reference/project-test-timing-baseline.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan-output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = build_manifest(
        collect_node_ids(root),
        historical_durations(root / args.junit),
        load_file_timing_baseline(root / args.timing_baseline),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.plan_output:
        plan = build_shard_plan(manifest, list(HOSTED_SHARDS))
        args.plan_output.parent.mkdir(parents=True, exist_ok=True)
        args.plan_output.write_text(
            json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(f"project-test manifest written: {args.output}")
    return 0


def build_manifest(
    node_ids: list[str],
    historical_durations_ms: dict[str, int],
    file_durations_ms: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Create one complete project-test manifest from live pytest collection.

    Historical durations influence scheduling only. An absent historical value
    receives a deterministic minimal weight, so newly added tests remain owned
    rather than disappearing from the shard plan.
    """
    if len(node_ids) != len(set(node_ids)):
        raise ManifestError("duplicate pytest node IDs are not allowed")
    file_durations_ms = file_durations_ms or {}
    nodes_per_file = Counter(node_id.split("::", 1)[0] for node_id in node_ids)
    entries: list[dict[str, Any]] = []
    for node_id in node_ids:
        if not isinstance(node_id, str) or not node_id.startswith("tests/") or "::" not in node_id:
            raise ManifestError(f"invalid pytest node ID: {node_id}")
        filename = node_id.split("::", 1)[0]
        file_fallback = max(1, round(file_durations_ms.get(filename, 0) / nodes_per_file[filename]))
        fallback = file_durations_ms.get(node_id, file_fallback)
        duration = historical_durations_ms.get(node_id, fallback)
        if not isinstance(duration, int) or isinstance(duration, bool) or duration < 0:
            raise ManifestError(f"invalid historical duration for {node_id}")
        entries.append({"id": node_id, "durationMs": duration, "kind": "pytest", "stage": "shard"})
    entries.extend(
        {"id": identifier, "durationMs": DEFAULT_DURATION_MS, "kind": kind, "stage": stage}
        for identifier, kind, stage in PROJECT_TEST_COMMANDS
    )
    return {"schemaVersion": 1, "nodeIds": node_ids, "entries": entries}


def _entries(entries: list[dict[str, Any]]) -> dict[str, int]:
    indexed: dict[str, int] = {}
    for entry in entries:
        identifier = entry.get("id")
        duration = entry.get("durationMs")
        if not isinstance(identifier, str) or not identifier:
            raise ManifestError("manifest entry id must be a non-empty string")
        if identifier in indexed:
            raise ManifestError(f"duplicate manifest entry: {identifier}")
        if not isinstance(duration, int) or isinstance(duration, bool) or duration < 0:
            raise ManifestError(f"manifest durationMs must be non-negative for {identifier}")
        indexed[identifier] = duration
    return indexed


def assign_shards(entries: list[dict[str, Any]], shards: list[str]) -> dict[str, list[str]]:
    """Greedily balance deterministic historical duration across named shards."""
    if not shards or any(not isinstance(shard, str) or not shard for shard in shards):
        raise ManifestError("at least one named shard is required")
    indexed = _entries(entries)
    assignments: dict[str, list[str]] = {shard: [] for shard in shards}
    loads: dict[str, int] = {shard: 0 for shard in shards}
    for identifier, duration in sorted(indexed.items(), key=lambda item: (-item[1], item[0])):
        shard = min(shards, key=lambda name: (loads[name], shards.index(name)))
        assignments[shard].append(identifier)
        loads[shard] += duration
    return assignments


def build_shard_plan(manifest: dict[str, Any], shards: list[str]) -> dict[str, Any]:
    """Bind the complete manifest to named duration-balanced Hosted shards."""
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ManifestError("manifest entries must be a list")
    shard_entries = [entry for entry in entries if entry.get("stage", "shard") == "shard"]
    aggregate_entries = [entry for entry in entries if entry.get("stage") == "aggregate"]
    unknown_stages = [
        entry.get("id")
        for entry in entries
        if entry.get("stage", "shard") not in {"shard", "aggregate"}
    ]
    if unknown_stages:
        raise ManifestError(
            f"unknown manifest stages: {', '.join(str(value) for value in unknown_stages)}"
        )
    assignments = assign_shards(shard_entries, shards)
    validate_assignments(shard_entries, assignments)
    aggregate_ids = [entry["id"] for entry in aggregate_entries]
    all_assignments = dict(assignments)
    all_assignments["aggregate"] = aggregate_ids
    validate_assignments(entries, all_assignments)
    durations = _entries(entries)
    return {
        "schemaVersion": 1,
        "entryCount": len(entries),
        "shards": assignments,
        "aggregateEntries": aggregate_ids,
        "loadsMs": {
            name: sum(durations[entry] for entry in values) for name, values in assignments.items()
        },
    }


def validate_assignments(entries: list[dict[str, Any]], assignments: dict[str, list[str]]) -> None:
    """Require every collected test or shell/E2E command to have one owner."""
    indexed = _entries(entries)
    owners: list[str] = []
    for shard, values in assignments.items():
        if not isinstance(shard, str) or not shard:
            raise ManifestError("shard name must be a non-empty string")
        if not isinstance(values, list):
            raise ManifestError(f"shard {shard} entries must be a list")
        owners.extend(values)
    unknown = sorted(set(owners).difference(indexed))
    if unknown:
        raise ManifestError(f"unknown manifest entries: {', '.join(unknown)}")
    counts = Counter(owners)
    duplicate = sorted(identifier for identifier, count in counts.items() if count > 1)
    if duplicate:
        raise ManifestError(
            f"manifest entries owned by more than one shard: {', '.join(duplicate)}"
        )
    unowned = sorted(set(indexed).difference(counts))
    if unowned:
        raise ManifestError(f"unowned manifest entries: {', '.join(unowned)}")


def validate_aggregate(
    receipts: list[dict[str, Any]], expected_shards: list[str], expected_source: dict[str, str]
) -> None:
    """Reject an aggregate unless every expected shard has complete exact-source evidence."""
    found: dict[str, dict[str, Any]] = {}
    for receipt in receipts:
        if not isinstance(receipt, dict):
            raise ManifestError("shard receipt must be an object")
        shard = receipt.get("shard")
        if not isinstance(shard, str) or not shard:
            raise ManifestError("shard receipt name must be a non-empty string")
        if shard in found:
            raise ManifestError(f"duplicate shard receipt: {shard}")
        found[shard] = receipt
    missing = sorted(set(expected_shards).difference(found))
    if missing:
        raise ManifestError(f"missing shard receipts: {', '.join(missing)}")
    unexpected = sorted(set(found).difference(expected_shards))
    if unexpected:
        raise ManifestError(f"unexpected shard receipts: {', '.join(unexpected)}")
    for shard in expected_shards:
        receipt = found[shard]
        if receipt.get("result") != "passed":
            raise ManifestError(f"shard {shard} result is not passed")
        for field in REQUIRED_SOURCE_FIELDS:
            if receipt.get(field) != expected_source.get(field):
                raise ManifestError(f"shard {shard} {field} does not match aggregate source")
        artifacts = receipt.get("artifacts")
        if not isinstance(artifacts, dict):
            raise ManifestError(f"shard {shard} artifacts must be an object")
        for artifact in REQUIRED_ARTIFACTS:
            if not isinstance(artifacts.get(artifact), str) or not artifacts[artifact]:
                raise ManifestError(f"shard {shard} missing {artifact} artifact")


if __name__ == "__main__":
    raise SystemExit(main())
