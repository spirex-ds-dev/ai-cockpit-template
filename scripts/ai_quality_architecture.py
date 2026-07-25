#!/usr/bin/env python3
"""Validate the repository's executable quality and test-layer contract.

This is intentionally a small, deterministic boundary check.  It does not
claim that static inspection proves production or provider safety; it only
fails closed on a few locally observable patterns and reports which test
layers have evidence in this checkout.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "target" / "quality_architecture_report.json"
TEST_LAYERS = {
    "unit": ("test_",),
    "schema": ("schema", "contract"),
    "state_machine": ("state", "lifecycle", "recovery"),
    "property": ("property", "fuzz", "corpus"),
    "transaction": ("transaction", "rollback"),
    "installer_integration": ("installer", "install"),
    "adopter_fixture": ("adopter", "fixture"),
    "hosted_smoke": ("hosted", "smoke"),
    "security_regression": ("security", "supply_chain", "secret"),
    "prompt_injection": ("injection", "trust"),
    "absurd": ("absurd", "delusion"),
    "release": ("release", "distribution"),
    "documentation": ("doc", "readme"),
}
SHELL_TRUE = re.compile(r"\bshell\s*=\s*True\b")
TRAVERSAL = re.compile(r"(?:/\.\./|\\\.\\\\|\.\.[/\\])")


def python_files(root: Path) -> list[Path]:
    return sorted((root / "scripts").glob("*.py"))


def test_files(root: Path) -> list[Path]:
    return sorted((root / "tests").glob("test_*.py"))


def inspect_source(path: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    # The checker necessarily contains the detection patterns themselves.
    if path.name == Path(__file__).name:
        return findings
    if path.is_symlink():
        return [{"kind": "symlink_input", "path": path.as_posix()}]
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError) as exc:
        kind = "encoding_error" if isinstance(exc, UnicodeDecodeError) else "parse_error"
        return [{"kind": kind, "path": path.as_posix(), "detail": str(exc)}]

    for line_number, line in enumerate(text.splitlines(), 1):
        if SHELL_TRUE.search(line):
            findings.append({"kind": "shell_true", "path": path.as_posix(), "line": line_number})
        if TRAVERSAL.search(line):
            findings.append(
                {"kind": "path_traversal_literal", "path": path.as_posix(), "line": line_number}
            )

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults = [*node.args.defaults, *(item for item in node.args.kw_defaults if item)]
            for default in defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    findings.append(
                        {
                            "kind": "mutable_default",
                            "path": path.as_posix(),
                            "line": default.lineno,
                            "function": node.name,
                        }
                    )
    return findings


def classify_tests(paths: list[Path]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for layer, tokens in TEST_LAYERS.items():
        matches = [
            path.as_posix() for path in paths if any(token in path.stem.lower() for token in tokens)
        ]
        result[layer] = {
            "status": "verified" if matches else "not_applicable",
            "evidence": matches,
            "reason": "matching repository test files"
            if matches
            else "no repository fixture for this layer",
        }
    return result


def build_report(root: Path) -> dict[str, Any]:
    findings = [finding for path in python_files(root) for finding in inspect_source(path)]
    layers = classify_tests(test_files(root))
    return {
        "schemaVersion": 1,
        "scope": "local repository quality architecture",
        "limitations": [
            "This report does not verify external provider, adopter, identity, or production controls.",
            "A matching test filename is evidence of a layer, not proof that every behavior is covered.",
        ],
        "safetyFindings": findings,
        "testLayers": layers,
        "status": "fail" if findings else "pass",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = build_report(args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"status": report["status"], "findings": len(report["safetyFindings"])},
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
