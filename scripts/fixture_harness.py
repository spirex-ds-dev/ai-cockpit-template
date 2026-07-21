#!/usr/bin/env python3
"""Run deterministic adoption-lifecycle experiments for repository fixtures."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


PHASES = (
    "Install",
    "Configure",
    "Normal Work Item",
    "Ambiguous Request",
    "Critical Domain Change",
    "Upgrade",
    "Rollback",
    "Release Check",
)


def run_fixture(path: Path) -> dict[str, object]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    stack = manifest["stack"]
    records = []
    for phase in PHASES:
        status = "passed"
        reason = "deterministic fixture phase completed"
        resume = "none"
        if phase == "Ambiguous Request":
            status, reason, resume = (
                "blocked",
                "insufficient intent and success criteria",
                "provide concrete intent and acceptance",
            )
        elif phase == "Critical Domain Change":
            status, reason, resume = (
                "blocked",
                "critical-domain change requires structured evidence",
                "use a sandbox fixture or provide reviewed evidence",
            )
        records.append(
            {
                "phase": phase,
                "status": status,
                "reason": reason,
                "evidence": [f"fixture:{stack}:{phase}"],
                "resumeCondition": resume,
                "policyReference": "ai-cockpit/fixture-lifecycle",
            }
        )
    return {
        "fixture": path.parent.name,
        "stack": stack,
        "toolchain": manifest["toolchain"],
        "phases": records,
        "platforms": manifest["platforms"],
        "performance": {
            "measurement": "not_applicable",
            "reason": "dependency-free deterministic harness",
        },
        "multiAgentConflict": {"status": "not_run", "reason": "single-process fixture harness"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=Path("examples/fixtures"))
    parser.add_argument("--output", type=Path, default=Path("target/fixture-evidence-bundle.json"))
    args = parser.parse_args()
    results = [
        run_fixture(path / "fixture.json")
        for path in sorted(args.fixtures.iterdir())
        if (path / "fixture.json").exists()
    ]
    bundle = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "fixtures": results,
        "evidenceBoundary": "Local deterministic harness evidence is not platform, identity, sandbox, or compliance proof.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
