"""Pure verification and acceptance signal policies."""

from __future__ import annotations
from typing import Any


def verification_signal(required: list[str], index: dict[str, str]) -> dict[str, Any]:
    missing = [x for x in required if x not in index]
    failed = [x for x in required if index.get(x) == "failed"]
    not_run = [x for x in required if index.get(x) == "not_run"]
    passed = [x for x in required if index.get(x) == "passed"]
    if failed:
        value, evidence = "failed", [f"required verification failed: {', '.join(failed)}"]
    elif missing or not_run:
        detail = []
        if missing:
            detail.append(f"missing: {', '.join(missing)}")
        if not_run:
            detail.append(f"not_run: {', '.join(not_run)}")
        value, evidence = "incomplete", [f"required verification incomplete ({'; '.join(detail)})"]
    else:
        value, evidence = "passed", [f"required verification passed: {len(passed)}/{len(required)}"]
    return {
        "value": value,
        "evidence": evidence,
        "sources": ["contract.verification", "summary.verification"],
        "required": required,
        "passed": passed,
        "failed": failed,
        "missing": missing,
        "not_run": not_run,
    }
