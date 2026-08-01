"""Build profile performance baselines from immutable local quality summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _p95(values: list[int]) -> int:
    return sorted(values)[max(0, (len(values) * 95 + 99) // 100 - 1)]


def build_baseline(summaries: list[dict[str, Any]], *, minimum_samples: int = 3) -> dict[str, Any]:
    """Return only measured local profile facts; unknown profiles stay excluded."""
    samples: dict[str, list[int]] = {}
    for summary in summaries:
        report = summary.get("performanceReport", {})
        if not isinstance(report, dict):
            continue
        profile = report.get("profile")
        duration = report.get("totalDurationMs")
        if profile in {None, "unknown"} or not isinstance(duration, int):
            continue
        samples.setdefault(str(profile), []).append(duration)
    profiles = {
        profile: {
            "sampleCount": len(values),
            "status": "baseline_ready" if len(values) >= minimum_samples else "collecting",
            "p95Ms": _p95(values) if len(values) >= minimum_samples else None,
        }
        for profile, values in sorted(samples.items())
    }
    return {
        "schemaVersion": 1,
        "measurementSource": "local_quality_summaries",
        "minimumSamples": minimum_samples,
        "profiles": profiles,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--minimum-samples", type=int, default=3)
    args = parser.parse_args()
    summaries = [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.input]
    report = build_baseline(summaries, minimum_samples=args.minimum_samples)
    Path(args.output).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
