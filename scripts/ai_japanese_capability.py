"""Deterministic, fail-closed Japanese repository-governance assessment.

This module evaluates evidence that belongs to the repository. It does not
grade a provider model's general Japanese fluency or replace human linguistic
review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from ai_input_trust import SourceType, assess_input, re_evaluate_high_risk_operation


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "tests/fixtures/japanese-capability-corpus.json"
JSON_REPORT_PATH = ROOT / "docs/reference/japanese-capability-assessment.json"
MARKDOWN_REPORT_PATH = ROOT / "docs/reference/japanese-capability-assessment.md"

REQUIRED_JA_DOCS = (
    "README.ja.md",
    "docs/overview.ja.md",
    "docs/getting-started/installation.ja.md",
    "docs/getting-started/first-work-item.ja.md",
    "docs/reference/how-to-read-cockpit-status.ja.md",
    "docs/reference/repository-workflow.ja.md",
    "docs/reference/work-item-lifecycle-closure.ja.md",
    "docs/reference/troubleshooting.ja.md",
    "docs/reference/upgrade.ja.md",
    "docs/reference/distribution.ja.md",
    "docs/reference/calibration-session.ja.md",
)

FINDINGS = {
    "JA-CLI-001": {
        "correctiveWorkItem": "japanese-wizard-cli-corrective-20260729",
        "summary": "Executable Wizard entrypoints do not consume Japanese locale resources.",
    },
    "JA-STATUS-001": {
        "correctiveWorkItem": "japanese-status-output-corrective-20260729",
        "summary": "Cockpit Status has no Japanese derived view or executable parity evidence.",
    },
    "JA-PR-001": {
        "correctiveWorkItem": "japanese-pr-output-corrective-20260729",
        "summary": "Task Outcome PR summary chrome is English-only.",
    },
    "JA-LIFECYCLE-001": {
        "correctiveWorkItem": "japanese-lifecycle-fixture-corrective-20260729",
        "summary": "No executable Japanese adopter fixture covers the governed lifecycle.",
    },
    "JA-DOC-001": {
        "correctiveWorkItem": "japanese-uninstall-documentation-corrective-20260729",
        "summary": "The Japanese engineer path lacks an actionable uninstall procedure.",
    },
}


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _read(relative: str) -> str:
    path = ROOT / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _case(
    case_id: str,
    area: str,
    status: str,
    observation: str,
    *,
    source: list[str],
    tests: list[str],
    commands: list[str],
    limitation: str,
    finding_id: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "id": case_id,
        "area": area,
        "status": status,
        "observation": observation,
        "sourceEvidence": source,
        "testEvidence": tests,
        "commandEvidence": commands,
        "limitation": limitation,
    }
    if finding_id is not None:
        value["findingId"] = finding_id
    value["digest"] = _digest(value)
    return value


def _load_corpus() -> dict[str, Any]:
    value = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("corpusVersion") != 1:
        raise ValueError("Japanese capability corpus must use corpusVersion 1")
    entries = value.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Japanese capability corpus entries must be a non-empty list")
    return value


def _evaluate_corpus() -> tuple[bool, bool, str]:
    failures: list[str] = []
    stop_failures: list[str] = []
    for entry in _load_corpus()["entries"]:
        if not isinstance(entry, dict):
            failures.append("non-object-entry")
            continue
        try:
            record = assess_input(SourceType(entry["sourceType"]), entry["content"])
        except (KeyError, TypeError, ValueError) as exc:
            failures.append(f"{entry.get('id', 'unknown')}:{exc}")
            continue
        expected_outcomes = entry.get("expectedOutcomes", [])
        if (
            record.instructionAuthority != entry.get("expectedAuthority")
            or record.outcome not in expected_outcomes
        ):
            failures.append(
                f"{entry.get('id')}:authority={record.instructionAuthority},outcome={record.outcome}"
            )
        operation = entry.get("highRiskOperation")
        if operation:
            decision = re_evaluate_high_risk_operation(record, operation)
            if decision.allowed or decision.outcome != "human_confirmation_required":
                stop_failures.append(str(entry.get("id")))
    observation = (
        f"{len(_load_corpus()['entries'])} corpus entries preserved authority and expected outcomes"
        if not failures
        else "corpus mismatches: " + "; ".join(failures)
    )
    return not failures, not stop_failures, observation


def _wizard_is_executable() -> bool:
    entrypoints = (
        ROOT / "scripts/ai_install_wizard.py",
        ROOT / "scripts/ai_calibration_wizard.py",
    )
    executable_tests = (
        (
            ROOT / "tests/test_install_wizard.py",
            "test_japanese_dry_run_uses_executable_locale_resources",
        ),
        (
            ROOT / "tests/test_calibration_wizard.py",
            "test_japanese_render_and_pause_use_executable_locale_resources",
        ),
    )
    return all(
        path.is_file()
        and "ai_wizard_localization" in path.read_text(encoding="utf-8")
        and "--language" in path.read_text(encoding="utf-8")
        for path in entrypoints
    ) and all(
        path.is_file() and test_name in path.read_text(encoding="utf-8")
        for path, test_name in executable_tests
    )


def _status_has_japanese_view() -> bool:
    text = _read("scripts/ai_generate_status.py")
    return "ja" in text and ("状態" in text or "Japanese" in text)


def _pr_has_japanese_view() -> bool:
    text = _read("scripts/ai_render_task_outcome_pr.py")
    return "ja" in text and ("状態" in text or "Japanese" in text)


def _task_outcome_has_japanese_view() -> bool:
    implementation = _read("scripts/ai_render_task_outcome_multilingual.py")
    tests = _read("tests/test_task_outcome_multilingual.py")
    return '"ja": {' in implementation and "## 概要" in tests


def _lifecycle_fixture_exists() -> bool:
    return (ROOT / "tests/test_japanese_adopter_lifecycle.py").is_file()


def _uninstall_path_exists() -> bool:
    terms = ("アンインストール", "uninstall")
    documents = (
        _read("docs/getting-started/installation.ja.md"),
        _read("docs/reference/upgrade.ja.md"),
        _read("README.ja.md"),
    )
    return any(any(term in text for term in terms) for text in documents)


def _documents_present() -> tuple[bool, list[str]]:
    missing = [relative for relative in REQUIRED_JA_DOCS if not (ROOT / relative).is_file()]
    return not missing, missing


def _release_gate_is_wired() -> bool:
    makefile = _read("Makefile")
    return (
        "check-japanese-capability:" in makefile
        and "scripts/ai_japanese_capability.py --check" in makefile
        and "check-release-preflight: check-japanese-capability" in makefile
    )


def evaluate() -> dict[str, Any]:
    corpus_pass, high_risk_pass, corpus_observation = _evaluate_corpus()
    docs_pass, missing_docs = _documents_present()
    cases = [
        _case(
            "JA-INPUT-001",
            "Japanese register, mixed technical language, encoded input, Unicode, and paths",
            "pass" if corpus_pass else "block",
            corpus_observation,
            source=["tests/fixtures/japanese-capability-corpus.json", "scripts/ai_input_trust.py"],
            tests=["tests/test_japanese_capability.py", "tests/test_input_trust_corpus.py"],
            commands=[
                "PYTHONPATH=scripts .venv/bin/pytest -q tests/test_japanese_capability.py tests/test_input_trust_corpus.py"
            ],
            limitation="Deterministic classification is not general semantic understanding.",
        ),
        _case(
            "JA-HIGH-RISK-001",
            "Japanese high-risk, absurd, Unknown, and human-confirmation STOP boundary",
            "pass" if high_risk_pass else "block",
            "Every corpus high-risk operation requires human_confirmation_required"
            if high_risk_pass
            else "One or more Japanese high-risk entries lost the STOP boundary",
            source=["tests/fixtures/japanese-capability-corpus.json", "scripts/ai_input_trust.py"],
            tests=["tests/test_japanese_capability.py", "tests/test_input_trust.py"],
            commands=[
                "PYTHONPATH=scripts .venv/bin/pytest -q tests/test_japanese_capability.py tests/test_input_trust.py"
            ],
            limitation="The policy boundary does not authenticate the human or execute provider controls.",
        ),
        _case(
            "JA-CLI-001",
            "Executable Wizard and CLI Japanese interaction",
            "pass" if _wizard_is_executable() else "block",
            "Both Wizard entrypoints consume the strict Japanese resource layer with executable tests"
            if _wizard_is_executable()
            else FINDINGS["JA-CLI-001"]["summary"],
            source=[
                "scripts/ai_wizard_localization.py",
                "scripts/ai_install_wizard.py",
                "scripts/ai_calibration_wizard.py",
                "locales/wizard/ja.json",
            ],
            tests=[
                "tests/test_wizard_localization.py",
                "tests/test_install_wizard.py",
                "tests/test_calibration_wizard.py",
            ],
            commands=[
                "PYTHONPATH=scripts .venv/bin/pytest -q tests/test_wizard_localization.py tests/test_install_wizard.py tests/test_calibration_wizard.py"
            ],
            limitation="Resource parity alone cannot prove executable Japanese interaction.",
            finding_id=None if _wizard_is_executable() else "JA-CLI-001",
        ),
        _case(
            "JA-STATUS-001",
            "Cockpit Status Japanese parity",
            "pass" if _status_has_japanese_view() else "block",
            "Japanese Status view is derived from the same machine facts"
            if _status_has_japanese_view()
            else FINDINGS["JA-STATUS-001"]["summary"],
            source=["scripts/ai_generate_status.py", ".ai/cockpit/current_status.md"],
            tests=["tests/test_core_gates.py"],
            commands=["make generate-cockpit-status"],
            limitation="A Japanese guide to an English Status is not output parity.",
            finding_id=None if _status_has_japanese_view() else "JA-STATUS-001",
        ),
        _case(
            "JA-PR-001",
            "Task Outcome PR summary Japanese parity",
            "pass" if _pr_has_japanese_view() else "block",
            "Japanese PR chrome preserves the approved field set"
            if _pr_has_japanese_view()
            else FINDINGS["JA-PR-001"]["summary"],
            source=["scripts/ai_render_task_outcome_pr.py"],
            tests=["tests/test_task_outcome_pr_summary.py"],
            commands=["PYTHONPATH=. .venv/bin/pytest -q tests/test_task_outcome_pr_summary.py"],
            limitation="PR localization must not translate or invent arbitrary evidence prose.",
            finding_id=None if _pr_has_japanese_view() else "JA-PR-001",
        ),
        _case(
            "JA-TASK-OUTCOME-001",
            "Task Outcome Japanese derived view",
            "pass" if _task_outcome_has_japanese_view() else "block",
            "Japanese Task Outcome chrome is derived from unchanged machine facts"
            if _task_outcome_has_japanese_view()
            else "Japanese Task Outcome parity evidence is missing",
            source=["scripts/ai_render_task_outcome_multilingual.py"],
            tests=["tests/test_task_outcome_multilingual.py"],
            commands=["PYTHONPATH=. .venv/bin/pytest -q tests/test_task_outcome_multilingual.py"],
            limitation="Arbitrary evidence prose remains source text and is not machine-translated.",
        ),
        _case(
            "JA-LIFECYCLE-001",
            "Executable Japanese adopter lifecycle",
            "pass" if _lifecycle_fixture_exists() else "block",
            "Japanese adopter fixture covers installation through recovery and removal"
            if _lifecycle_fixture_exists()
            else FINDINGS["JA-LIFECYCLE-001"]["summary"],
            source=["docs/getting-started/installation.ja.md"],
            tests=["tests/test_japanese_adopter_lifecycle.py"],
            commands=["PYTHONPATH=. .venv/bin/pytest -q tests/test_japanese_adopter_lifecycle.py"],
            limitation="English lifecycle fixtures cannot be used to infer Japanese operator usability.",
            finding_id=None if _lifecycle_fixture_exists() else "JA-LIFECYCLE-001",
        ),
        _case(
            "JA-DOC-001",
            "Japanese installation, calibration, upgrade, rollback, uninstall, and recovery path",
            "pass" if docs_pass and _uninstall_path_exists() else "block",
            "All required Japanese documents and an actionable uninstall path are present"
            if docs_pass and _uninstall_path_exists()
            else (
                FINDINGS["JA-DOC-001"]["summary"]
                + (f"; missing documents: {', '.join(missing_docs)}" if missing_docs else "")
            ),
            source=list(REQUIRED_JA_DOCS),
            tests=["tests/test_docs_metadata.py"],
            commands=["make check-docs-metadata"],
            limitation="Structure and terminology checks do not replace native technical editing.",
            finding_id=None if docs_pass and _uninstall_path_exists() else "JA-DOC-001",
        ),
        _case(
            "JA-DOC-STRUCTURE-001",
            "Japanese document metadata and three-language structure",
            "pass" if docs_pass else "block",
            "Required Japanese engineer entry documents exist and remain under metadata checks"
            if docs_pass
            else f"missing documents: {', '.join(missing_docs)}",
            source=list(REQUIRED_JA_DOCS),
            tests=["tests/test_docs_metadata.py", "tests/test_trust_layer_docs.py"],
            commands=["make check-docs-metadata", "make check-trust-layer-docs"],
            limitation="Automated parity checks cannot establish complete translation quality.",
        ),
        _case(
            "JA-RELEASE-GATE-001",
            "Mandatory pre-release Japanese evidence gate",
            "pass" if _release_gate_is_wired() else "block",
            "check-release-preflight requires the current Japanese assessment"
            if _release_gate_is_wired()
            else "release preflight does not invoke the Japanese assessment",
            source=["Makefile", "scripts/ai_japanese_capability.py"],
            tests=["tests/test_makefile.py", "tests/test_japanese_capability.py"],
            commands=["make check-japanese-capability", "make check-release-preflight"],
            limitation="Passing the gate proves only the in-repository matrix at the assessed source.",
        ),
        _case(
            "JA-GENERAL-FLUENCY",
            "General Japanese model fluency and human translation quality",
            "limitation",
            "No provider-backed or native-human-reviewed general fluency evidence is claimed.",
            source=[],
            tests=[],
            commands=[],
            limitation="General Japanese provider/model fluency and human translation quality remain unproved.",
        ),
    ]
    blocking_findings = []
    for case in cases:
        finding_id = case.get("findingId")
        if case["status"] == "block" and isinstance(finding_id, str):
            blocking_findings.append(
                {
                    "id": finding_id,
                    "caseId": case["id"],
                    **FINDINGS[finding_id],
                }
            )
    result: dict[str, Any] = {
        "assessmentVersion": 2,
        "workItemId": "japanese-assessment-depth-corrective-20260729",
        "scope": "bounded repository-governance Japanese handling",
        "corpus": {
            "path": str(CORPUS_PATH.relative_to(ROOT)),
            "digest": _digest(_load_corpus()),
            "entryCount": len(_load_corpus()["entries"]),
        },
        "cases": cases,
        "blockingFindings": blocking_findings,
        "limitations": [
            "This assessment does not claim general model fluency, translation quality, or provider behavior.",
            "Every English-inferred, missing, stale, or non-executable Japanese capability is release-blocking.",
        ],
    }
    result["digest"] = _digest(result)
    return result


def render_json(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "---",
        "author: Ray",
        'title: "Japanese Capability Assessment"',
        "description: Comprehensive, bounded, evidence-backed Japanese repository-governance release gate.",
        "---",
        "",
        "# Japanese Capability Assessment",
        "",
        "> This is a release gate, not a claim of general Japanese model fluency.",
        "",
        f"- Work Item: `{result['workItemId']}`",
        f"- Assessment digest: `{result['digest']}`",
        f"- Corpus: `{result['corpus']['path']}` (`{result['corpus']['entryCount']}` entries)",
        f"- Blocking findings: `{len(result['blockingFindings'])}`",
        "",
        "## Evidence boundary",
        "",
        "The matrix evaluates current repository behavior, executable evidence, and Japanese engineer paths. Missing or English-inferred evidence is blocking. General provider/model fluency and native-human translation review remain explicit non-claims.",
        "",
        "## Matrix",
        "",
        "| ID | Area | Status | Observation | Source / tests / commands |",
        "| --- | --- | --- | --- | --- |",
    ]
    for case in result["cases"]:
        evidence = [
            *(f"`{item}`" for item in case["sourceEvidence"]),
            *(f"`{item}`" for item in case["testEvidence"]),
            *(f"`{item}`" for item in case["commandEvidence"]),
        ]
        observation = case["observation"].replace("|", "\\|")
        lines.append(
            f"| `{case['id']}` | {case['area']} | **{case['status']}** | "
            f"{observation} | {'; '.join(evidence) or 'none'} |"
        )
    lines.extend(["", "## Blocking findings", ""])
    if result["blockingFindings"]:
        for finding in result["blockingFindings"]:
            lines.append(
                f"- `{finding['id']}`: {finding['summary']} Corrective Work Item: "
                f"`{finding['correctiveWorkItem']}`."
            )
    else:
        lines.append("- None within the declared repository-governance scope.")
    lines.extend(
        [
            "",
            "Each blocker requires its own Contract, implementation, verification, PR, Hosted CI, merge, `make ai-close-work-item`, branch cleanup, and a fresh assessment. A blocker cannot be cleared by editing this report.",
            "",
            "## Reproduce",
            "",
            "```bash",
            "PYTHONPATH=scripts .venv/bin/python scripts/ai_japanese_capability.py --check",
            "```",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in result["limitations"])
    return "\n".join(lines) + "\n"


def report_drift(result: dict[str, Any], *, json_path: Path, markdown_path: Path) -> list[str]:
    errors: list[str] = []
    expected_json = render_json(result)
    expected_markdown = render_markdown(result)
    if not json_path.is_file() or json_path.read_text(encoding="utf-8") != expected_json:
        errors.append(f"stale Japanese assessment JSON: {json_path}")
    if (
        not markdown_path.is_file()
        or markdown_path.read_text(encoding="utf-8") != expected_markdown
    ):
        errors.append(f"stale Japanese assessment Markdown: {markdown_path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write JSON and Markdown reports")
    mode.add_argument("--check", action="store_true", help="verify checked-in reports")
    args = parser.parse_args()
    result = evaluate()
    if args.write:
        JSON_REPORT_PATH.write_text(render_json(result), encoding="utf-8")
        MARKDOWN_REPORT_PATH.write_text(render_markdown(result), encoding="utf-8")
    if args.check:
        errors = report_drift(
            result, json_path=JSON_REPORT_PATH, markdown_path=MARKDOWN_REPORT_PATH
        )
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 2
    print(render_json(result), end="")
    if result["blockingFindings"]:
        print(
            "Japanese capability assessment is release-blocking: "
            + ", ".join(finding["id"] for finding in result["blockingFindings"]),
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
