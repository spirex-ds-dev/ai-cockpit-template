#!/usr/bin/env python3
"""Run finish checks for a Work Item through the Makefile."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai_acceptance_policy import validate_acceptance_evidence
from ai_check_diff_ownership import format_preview, preview
from ai_common import (
    PROJECT_ROOT,
    changed_paths,
    clean_git_environment,
    current_head,
    discover_remote_default_candidates,
    included,
    load_json,
    nested_make_command,
    path_fingerprint,
    redact_machine_paths,
    redact_sensitive_output,
    render_check_command,
    run_git,
    save_json,
    verification_key,
)
from ai_observability import create_observability, elapsed_ms
from ai_work_item_intelligence import record_fact_once

ACTIVE_DIR = PROJECT_ROOT / ".ai" / "work-items" / "active"
FINISH_LOCK_MAX_AGE_SECONDS = 24 * 60 * 60
REPORT_BOUNDARY_TEXT = {
    "en": (
        "## Task Outcome Report (active; relay to the human before archive)",
        "Next lifecycle action: archive is explicit and must follow the direct human report.",
    ),
    "zh-CN": (
        "## 工单结果报告（active；归档前必须直接告知相关人员）",
        "下一生命周期动作：归档必须显式执行，并且只能在直接报告之后进行。",
    ),
    "ja": (
        "## タスク結果レポート（active。アーカイブ前に直接人へ報告してください）",
        "次のライフサイクル操作：アーカイブは明示的に実行し、直接報告の後にのみ行います。",
    ),
}


def checkpoint_recovery_guidance(issues: list[str], *, contract: str, summary: str) -> str:
    """Return the canonical non-bypass recovery command for checkpoint failures."""
    missing_before_finish = any(
        "missing checkpointEvidence for required stage(s):" in issue and "before_finish" in issue
        for issue in issues
    )
    if missing_before_finish:
        return (
            "ERROR: Required before_finish checkpoint evidence is missing; run "
            f"make ai-checkpoint CONTRACT={contract} SUMMARY={summary} "
            "STAGE=before_finish before retrying ai-finish."
        )
    stale_before_edit = any(
        "contract_amendment_revalidation" in issue or "before_edit" in issue and "stale" in issue
        for issue in issues
    )
    if stale_before_edit:
        return (
            "ERROR: Immutable before_edit Contract binding is stale; run "
            f"make ai-revalidate-contract-amendment CONTRACT={contract} SUMMARY={summary} "
            "PREVIOUS_CONTRACT_HASH=<immutable-before-edit-hash> "
            "AMENDMENT_REASON='<why the Contract changed>' before retrying ai-finish."
        )
    return (
        "ERROR: Checkpoint validation failed; inspect every reported checkpoint issue, "
        "preserve active evidence, and use only the stage-specific canonical recovery "
        "command before retrying ai-finish."
    )


class FinishMutexError(RuntimeError):
    """Raised when another Finish owns this Work Item worktree."""


def _finish_lock_path(task: str, *, root: Path) -> Path:
    """Return an untracked lock location unique to this worktree and task."""
    result = subprocess.run(  # nosec B603 B607 - fixed list-form Git metadata lookup
        ["git", "rev-parse", "--git-dir"],
        cwd=root,
        env=clean_git_environment(),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        git_dir = Path(result.stdout.strip())
        if not git_dir.is_absolute():
            git_dir = root / git_dir
        return git_dir / f"ai-finish-{task}.lock"
    return root / ".ai" / "work-items" / "runtime" / f"ai-finish-{task}.lock"


def _load_finish_lock_metadata(lock_path: Path) -> dict[str, Any]:
    try:
        value = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _metadata_is_stale(metadata: dict[str, Any], *, now: datetime) -> bool:
    value = metadata.get("startedAt")
    if not isinstance(value, str):
        return False
    try:
        started = datetime.fromisoformat(value)
    except ValueError:
        return False
    if started.tzinfo is None:
        return False
    return (now - started.astimezone(UTC)).total_seconds() > FINISH_LOCK_MAX_AGE_SECONDS


@contextlib.contextmanager
def finish_mutex(
    task: str,
    *,
    archive: bool,
    root: Path = PROJECT_ROOT,
) -> Any:
    """Serialize Finish only for one task in one worktree.

    Advisory metadata makes the owner/retry route observable.  The kernel lock
    is authoritative, automatically released on process death, and therefore
    cannot turn a crashed Finish into an unbounded stale lock.
    """
    lock_path = _finish_lock_path(task, root=root)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            handle.seek(0)
            owner = _load_finish_lock_metadata(lock_path)
            owner_pid = owner.get("pid", "unknown")
            owner_mode = "archive" if owner.get("archive") is True else "normal"
            requested_mode = "archive" if archive else "normal"
            raise FinishMutexError(
                "ai-finish is already running for this Work Item worktree "
                f"(task={task}, owner_pid={owner_pid}, owner_mode={owner_mode}, "
                f"requested_mode={requested_mode}). Wait for the owner to finish, then retry; "
                "do not remove or edit active evidence or the mutex file."
            ) from exc
        now = datetime.now(UTC)
        previous = _load_finish_lock_metadata(lock_path)
        if _metadata_is_stale(previous, now=now):
            print(
                "Recovered stale ai-finish mutex metadata after kernel-lock acquisition "
                f"(task={task}, previous_pid={previous.get('pid', 'unknown')}).",
                file=sys.stderr,
            )
        metadata = {
            "task": task,
            "pid": os.getpid(),
            "startedAt": now.isoformat(),
            "archive": archive,
            "worktree": root.resolve().as_posix(),
        }
        handle.seek(0)
        handle.truncate()
        json.dump(metadata, handle, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        try:
            yield
        finally:
            handle.seek(0)
            handle.truncate()
            handle.flush()
            os.fsync(handle.fileno())
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _git_output(args: list[str]) -> str:
    result = run_git(args)
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {(result.stderr or result.stdout).strip()}"
        )
    return result.stdout.strip()


def repository_base_branch() -> str | None:
    candidates = discover_remote_default_candidates(run_git)
    if len(candidates) > 1:
        raise RuntimeError(
            "could not uniquely discover the repository remote default branch; "
            "multiple remote HEAD targets were found"
        )
    return candidates[0][1] if candidates else None


def ensure_work_item_branch() -> None:
    current = _git_output(["branch", "--show-current"])
    base = repository_base_branch()
    if base is not None:
        validate_work_item_branch(current, base)


def validate_work_item_branch(current: str, base: str) -> None:
    if current == base:
        raise RuntimeError(
            "ai-finish must run on the dedicated Work Item branch; current branch is the repository "
            f"base branch ({base}). Finish/archive on the Work Item branch before pushing and opening the PR."
        )


def task_paths(task: str) -> tuple[str, str]:
    contract = ACTIVE_DIR / f"{task}.contract.json"
    summary = ACTIVE_DIR / f"{task}.summary.json"
    return contract.relative_to(PROJECT_ROOT).as_posix(), summary.relative_to(
        PROJECT_ROOT
    ).as_posix()


def run(command: list[str], *, extra_env: dict[str, str] | None = None) -> tuple[int, int, str]:
    command = list(command)
    if command and command[0] == "make":
        for name in ("PROJECT_FORMAT_CHECK", "PROJECT_TEST", "PROJECT_LINT"):
            if name in os.environ and not any(item.startswith(f"{name}=") for item in command):
                command.append(f"{name}={os.environ[name]}")
    try:
        command = nested_make_command(command, root=PROJECT_ROOT)
    except ValueError as exc:
        output = f"ERROR: {exc}\n"
        print(output, end="", file=sys.stderr)
        return 2, 0, output
    print("$ " + " ".join(command))
    start = time.time()
    environment = clean_git_environment()
    if extra_env:
        environment.update(extra_env)
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.stdout:
        displayed = console_output(result.stdout)
        print(displayed, end="" if displayed.endswith("\n") else "\n")
    return result.returncode, elapsed_ms(start), result.stdout or ""


def evidence(
    check_id: str,
    command: str,
    code: int,
    duration: int,
    output: str,
    *,
    contract_hash: str,
    commit_sha: str,
    execution_contract_path: str,
    execution_summary_path: str,
    worktree_digest: str,
) -> dict[str, Any]:
    compact = redact_sensitive_output(output)
    compact = redact_machine_paths(compact)
    compact = " ".join(compact.split())[:500]
    tail = redact_sensitive_output(output)
    tail = redact_machine_paths(tail)
    tail = " ".join(tail.split())[-2000:]
    return {
        "check": check_id,
        "command": command,
        "result": "passed" if code == 0 else "failed",
        "runner": "ai_finish",
        "executedAt": datetime.now(UTC).isoformat(),
        "exitCode": code,
        "durationMs": duration,
        "outputDigest": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        "commandHash": hashlib.sha256(" ".join(command.split()).encode("utf-8")).hexdigest(),
        "contractHash": contract_hash,
        "commitSha": commit_sha,
        "executionContractPath": execution_contract_path,
        "executionSummaryPath": execution_summary_path,
        "worktreeDigest": worktree_digest,
        "outputSummary": compact,
        "outputTail": tail,
        "outputBytes": len(output.encode("utf-8")),
    }


def pending_evidence(
    check_id: str,
    command: str,
    *,
    contract_hash: str,
    commit_sha: str,
    execution_contract_path: str,
    execution_summary_path: str,
    worktree_digest: str,
) -> dict[str, Any]:
    item = evidence(
        check_id,
        command,
        0,
        0,
        "pending transactional validation",
        contract_hash=contract_hash,
        commit_sha=commit_sha,
        execution_contract_path=execution_contract_path,
        execution_summary_path=execution_summary_path,
        worktree_digest=worktree_digest,
    )
    item["runner"] = "ai_finish_pending"
    return item


def worktree_digest(paths: list[str]) -> str:
    digest = hashlib.sha256()
    for path in sorted(set(paths)):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path_fingerprint(path).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def worktree_digest_for_finish(paths: list[str], summary_path: str) -> str:
    """Hash the Work Item state without the self-referential Summary file."""
    return worktree_digest([path for path in paths if path != summary_path])


def reusable_archive_verification(
    summary: dict[str, Any],
    contract_data: dict[str, Any],
    *,
    contract_hash: str,
    commit_sha: str,
    contract: str,
    summary_path: str,
) -> bool:
    """Return whether archive can consume a same-state finish attestation.

    `aiSummary` is written last and fingerprints every owned path except the
    self-referential Summary.  It is therefore the only reusable anchor: a
    prior pass from another commit, Contract, path, or worktree state is never
    sufficient to skip strict verification.
    """
    values = summary.get("verification")
    if not isinstance(values, list):
        return False
    expected_digest = worktree_digest_for_finish(changed_paths(contract_data), summary_path)
    return any(
        isinstance(item, dict)
        and item.get("check") == "aiSummary"
        and item.get("result") == "passed"
        and item.get("runner") == "ai_finish"
        and item.get("contractHash") == contract_hash
        and item.get("commitSha") == commit_sha
        and item.get("executionContractPath") == contract
        and item.get("executionSummaryPath") == summary_path
        and item.get("worktreeDigest") == expected_digest
        for item in values
    )


def record_result(summary_path: Path, item: dict[str, Any]) -> None:
    if not summary_path.exists():
        raise FileNotFoundError(f"summary not found: {summary_path.relative_to(PROJECT_ROOT)}")
    summary = load_json(summary_path)
    values = summary.get("verification", [])
    if not isinstance(values, list):
        values = []
    summary["verification"] = [
        entry
        for entry in values
        if not (isinstance(entry, dict) and verification_key(entry) == verification_key(item))
    ] + [item]
    save_json(summary_path, summary)


def promote_review_readiness(
    summary: dict[str, Any], contract: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Derive review readiness from recorded verification and residual risk."""
    verification = summary.get("verification")
    unknowns = summary.get("unknownsRemaining")
    required_checks: set[str] | None = None
    if isinstance(contract, dict) and contract.get("contractVersion") == 2:
        declared = contract.get("verification")
        if isinstance(declared, list):
            required_checks = {
                item["check"]
                for item in declared
                if isinstance(item, dict)
                and isinstance(item.get("check"), str)
                and item.get("required", True) is True
            }
    if isinstance(verification, list) and required_checks is not None:
        passed_required_checks = {
            item.get("check")
            for item in verification
            if isinstance(item, dict) and item.get("result") == "passed"
        }
        verification_complete = required_checks <= passed_required_checks
    else:
        verification_complete = (
            isinstance(verification, list)
            and bool(verification)
            and all(
                isinstance(item, dict) and item.get("result") == "passed" for item in verification
            )
        )
    complete = verification_complete and isinstance(unknowns, list) and not unknowns
    existing = summary.get("reviewReadiness")
    expected_focus = (
        existing.get("expectedReviewFocus", [])
        if isinstance(existing, dict) and isinstance(existing.get("expectedReviewFocus"), list)
        else []
    )
    if isinstance(contract, dict):
        acceptance_issues = validate_acceptance_evidence(
            contract,
            summary,
            summary.get("verification", [])
            if isinstance(summary.get("verification"), list)
            else [],
        )
        if acceptance_issues:
            return {
                "status": "not_ready",
                "reason": "Acceptance evidence is incomplete: " + "; ".join(acceptance_issues[:3]),
                "expectedReviewFocus": expected_focus,
            }
    if not complete:
        return {
            "status": "not_ready",
            "reason": "Required verification or known-unknown evidence is incomplete.",
            "expectedReviewFocus": expected_focus,
        }
    residual_risks = summary.get("residualRisks")
    has_residual_risk = isinstance(residual_risks, list) and bool(residual_risks)
    return {
        "status": "ready_with_risks" if has_residual_risk else "ready",
        "reason": (
            "All required verification passed; residual risk remains documented."
            if has_residual_risk
            else "All required verification passed and no residual risk remains."
        ),
        "expectedReviewFocus": expected_focus,
    }


def archive_next_steps(task: str) -> str:
    return (
        "Work Item archived; lifecycle is not closed. "
        "Next steps: push this Work Item branch, open and merge its PR, "
        f"then run make ai-close-work-item TASK={task}."
    )


def pre_archive_critical_coverage_command(
    contract_data: dict[str, Any],
) -> tuple[list[str] | None, str | None]:
    """Return the base-bound coverage gate that must precede archive mutation."""
    base_commit = contract_data.get("baseCommit")
    if not isinstance(base_commit, str) or not base_commit.strip():
        return None, "Contract baseCommit is required for pre-archive critical coverage"
    work_item_id = contract_data.get("workItemId")
    if not isinstance(work_item_id, str) or not work_item_id:
        return None, "pre-archive changed-critical coverage requires a Work Item id"
    return [
        "make",
        "check-changed-critical-coverage",
        f"AI_BASE_COMMIT={base_commit}",
        f"CONTRACT=.ai/work-items/active/{work_item_id}.contract.json",
    ], None


def run_pre_archive_critical_coverage(
    contract_data: dict[str, Any], *, obs: Any
) -> tuple[int, str]:
    """Run and record the archive-blocking critical coverage gate."""
    command, error = pre_archive_critical_coverage_command(contract_data)
    if command is None:
        return 2, error or "pre-archive critical coverage is unavailable"
    command_text = " ".join(command)
    obs.check_started(check_id="preArchiveCriticalCoverage", command=command_text)
    code, duration, output = run(command)
    if code:
        obs.check_failed(
            check_id="preArchiveCriticalCoverage", command=command_text, duration_ms=duration
        )
    else:
        obs.check_passed(
            check_id="preArchiveCriticalCoverage", command=command_text, duration_ms=duration
        )
    return code, output


def verification_priority(item: dict[str, Any]) -> int:
    check_id = verification_key(item)
    if check_id == "sourceBoundEvidence":
        return 0
    if check_id == "aiStatus":
        return 20
    if check_id == "aiStatusCheck":
        return 30
    if check_id == "aiStatusConsistency":
        return 40
    if check_id == "aiAgentRisk":
        return 50
    if check_id == "aiSummary":
        return 51
    return 10


def finish_execution_priority(item: dict[str, Any]) -> int:
    """Order ai-finish's self-referential gates around Outcome integration."""
    check_id = verification_key(item)
    if check_id == "aiSummary":
        return 100
    return verification_priority(item) + 10


STABILIZATION_CHECKS = frozenset(
    {"aiStatus", "aiStatusCheck", "aiStatusConsistency", "aiAgentRisk", "aiSummary"}
)
# Final source-bound reassessment is release evidence.  It must be requested
# by the release-stage Contract/target, not injected into every ordinary Work
# Item finish: a source-changing corrective must be able to complete its PR
# lifecycle before the post-merge reassessment can truthfully bind to HEAD.
MANDATORY_VERIFICATION_CHECKS: tuple[str, ...] = ()
CONSOLE_OUTPUT_LIMIT = 12_000


def console_output(output: str) -> str:
    """Keep terminal diagnostics bounded without weakening stored evidence."""
    if len(output) <= CONSOLE_OUTPUT_LIMIT:
        return output
    omitted = len(output) - CONSOLE_OUTPUT_LIMIT
    return (
        output[:CONSOLE_OUTPUT_LIMIT]
        + f"\n[output truncated: {omitted} character(s) retained in verification evidence]\n"
    )


def inject_mandatory_verification_checks(
    declared_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize explicitly declared checks without adding release-only gates."""
    normalized: dict[str, dict[str, Any]] = {
        check_id: {"check": check_id, "required": True}
        for check_id in MANDATORY_VERIFICATION_CHECKS
    }
    for item in declared_items:
        check_id = verification_key(item)
        if not check_id:
            continue
        current = normalized.get(check_id)
        if current is None:
            normalized[check_id] = dict(item)
            continue
        replacement = dict(item)
        replacement["required"] = current.get("required") is True or item.get("required") is True
        normalized[check_id] = replacement
    return list(normalized.values())


def _outcome_paths(task: str) -> tuple[Path, Path]:
    root = ACTIVE_DIR / task
    return root.with_suffix(".outcome.json"), root.with_suffix(".outcome.md")


def _human_report_paths() -> tuple[Path, Path]:
    root = PROJECT_ROOT / ".ai" / "cockpit" / "task_report"
    return root.with_suffix(".json"), root.with_suffix(".md")


def run_human_report_pipeline(task: str, summary_path: Path) -> tuple[bool, str]:
    """Generate the compact review view from the validated Task Outcome."""

    from ai_generate_human_report import generate_human_report, render_human_report

    outcome_path, _ = _outcome_paths(task)
    json_path, markdown_path = _human_report_paths()
    try:
        outcome = load_json(outcome_path)
        report = generate_human_report(outcome, phase="review")
        save_json(json_path, report)
        markdown_path.write_text(render_human_report(report), encoding="utf-8")
        summary = load_json(summary_path)
        changed = summary.setdefault("changedFiles", [])
        contract_path = PROJECT_ROOT / ".ai" / "work-items" / "active" / f"{task}.contract.json"
        contract = load_json(contract_path) if contract_path.is_file() else {}
        scope = contract.get("scope", []) if isinstance(contract, dict) else []
        existing = {item.get("path") for item in changed if isinstance(item, dict)}
        for path, reason in (
            (json_path, "Generated machine-readable Human Benefit Review Report."),
            (markdown_path, "Generated human-readable Human Benefit Review Report."),
        ):
            relative = path.relative_to(PROJECT_ROOT).as_posix()
            if included(relative, scope) and relative not in existing:
                changed.append({"path": relative, "reason": reason})
        alignment = summary.get("documentationAlignment")
        report_markdown = markdown_path.relative_to(PROJECT_ROOT).as_posix()
        outcome_markdown = _outcome_paths(task)[1].relative_to(PROJECT_ROOT).as_posix()
        documented_generated_paths = {
            report_markdown,
            outcome_markdown,
        }
        declared_after_generation = {item.get("path") for item in changed if isinstance(item, dict)}
        if isinstance(alignment, dict):
            checks = alignment.get("checks")
            if isinstance(checks, list):
                for check in checks:
                    if (
                        not isinstance(check, dict)
                        or check.get("area") != "documentationCommandsCapability"
                    ):
                        continue
                    evidence_paths = check.setdefault("evidence", [])
                    if isinstance(evidence_paths, list):
                        for generated_path in sorted(
                            candidate
                            for candidate in documented_generated_paths & declared_after_generation
                            if included(candidate, scope)
                        ):
                            if generated_path not in evidence_paths:
                                evidence_paths.append(generated_path)
                    break
        save_json(summary_path, summary)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return False, str(exc)
    return True, "Human Benefit Report pipeline passed"


def refresh_archived_human_report(task: str) -> tuple[bool, str]:
    """Rebind the Review Report after archive rewrites Outcome evidence paths."""

    from ai_generate_human_report import generate_human_report, render_human_report

    matches = sorted(
        (PROJECT_ROOT / ".ai" / "work-items" / "archive").glob(f"*/{task}.outcome.json")
    )
    if len(matches) != 1:
        return False, f"expected exactly one archived Task Outcome for {task}, found {len(matches)}"
    json_path, markdown_path = _human_report_paths()
    try:
        report = generate_human_report(load_json(matches[0]), phase="review")
        save_json(json_path, report)
        markdown_path.write_text(render_human_report(report), encoding="utf-8")
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return False, str(exc)
    return True, "Archived Human Benefit Report binding passed"


def _record_outcome_state(summary_path: Path, state: dict[str, Any]) -> None:
    summary = load_json(summary_path)
    status = state.get("status")
    if status == "completed":
        state.setdefault("humanStatusColor", "green")
        state.setdefault("completionFact", "All declared finish checks passed.")
        state.setdefault("recoveryCondition", "")
    elif status in {"blocked", "failed"}:
        state.setdefault("humanStatusColor", "red")
    else:
        state.setdefault("humanStatusColor", "yellow")
    summary["taskOutcome"] = state
    changed = summary.get("changedFiles")
    output_paths = (state.get("jsonPath"), state.get("markdownPath"))
    if isinstance(changed, list):
        declared = {
            item.get("path")
            for item in changed
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        }
        for path in output_paths:
            if isinstance(path, str) and path not in declared:
                changed.append(
                    {
                        "path": path,
                        "reason": "Mandatory Task Outcome evidence generated by ai-finish.",
                    }
                )
    save_json(summary_path, summary)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _pre_merge_outcome_input(task: str, contract_path: Path, summary_path: Path) -> dict[str, Any]:
    """Derive truthful Outcome evidence before a provider PR can exist."""
    contract = load_json(contract_path)
    summary = load_json(summary_path)
    head_commit = current_head()
    base_commit = contract.get("baseCommit")
    if not isinstance(base_commit, str) or len(base_commit) != 40:
        raise ValueError("Contract baseCommit is required for mandatory Task Outcome")
    if len(head_commit) != 40:
        raise ValueError("current HEAD is required for mandatory Task Outcome")
    changed = summary.get("changedFiles", [])
    delivered = [
        item["path"]
        for item in changed
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    ]
    warnings = [item for item in summary.get("knownGaps", []) if isinstance(item, str)]
    non_risk_explanations = [
        dict(item) for item in summary.get("nonRiskExplanations", []) if isinstance(item, dict)
    ]
    limitations = [
        {
            "sourceWarning": warning,
            "title": "Unresolved evidence is explicitly limited",
            "affectedClaims": ["completion_claim"],
            "requiredEvidence": ["fresh verification evidence"],
            "forbiddenClaims": ["Do not claim this warning was verified or resolved."],
        }
        for warning in warnings
    ]
    known_gap_non_risk_explanations = [
        {
            "sourceWarning": warning,
            "reason": "The Summary records this item as an unresolved gap rather than a verified result.",
            "evidence": [],
        }
        for warning in warnings
    ]
    human_decisions = [
        item["instruction"]
        for item in summary.get("userCorrectionsCaptured", [])
        if isinstance(item, dict) and isinstance(item.get("instruction"), str)
    ]
    verification = summary.get("verification", [])
    return {
        "taskId": task,
        "bindings": {
            "taskId": task,
            "contractDigest": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
            "summaryDigest": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
            "verificationDigest": _sha256_json(verification),
            "baseCommit": base_commit,
            "headCommit": head_commit,
            "lifecycleStage": "pre_merge",
            "pullRequest": {"state": "not_created"},
            "aiCockpitVersion": "repository-governance",
            "generatorVersion": "1.0",
        },
        "evidence": {
            "deliveredChanges": delivered,
            "warnings": warnings,
            "limitations": limitations,
            "nonRiskExplanations": [
                *non_risk_explanations,
                *known_gap_non_risk_explanations,
            ],
            "forbiddenClaims": ["Do not claim an unresolved warning was verified or resolved."]
            if warnings
            else [],
            "humanDecisions": human_decisions,
            "sources": [
                {
                    "source": contract_path.relative_to(PROJECT_ROOT).as_posix(),
                    "subject": "Contract",
                },
                {"source": summary_path.relative_to(PROJECT_ROOT).as_posix(), "subject": "Summary"},
            ],
        },
    }


def _write_and_validate_pre_merge_outcome(
    task: str, contract_path: Path, summary_path: Path, json_path: Path, markdown_path: Path
) -> tuple[bool, str]:
    from ai_check_task_outcome import validate_outcome
    from ai_generate_task_outcome import generate_outcome
    from ai_render_task_outcome import render_task_outcome

    try:
        payload = _pre_merge_outcome_input(task, contract_path, summary_path)
        outcome = generate_outcome(task, payload["bindings"], evidence=payload["evidence"])
        markdown = render_task_outcome(outcome)
        report = validate_outcome(outcome, markdown, expected_task_id=task)
        if not report.valid:
            return False, "; ".join(f"{item.code}: {item.message}" for item in report.errors)
        save_json(json_path, outcome)
        markdown_path.write_text(markdown, encoding="utf-8")
    except (OSError, ValueError) as exc:
        return False, str(exc)
    return True, "Outcome pipeline passed"


def write_blocked_outcome(
    task: str,
    contract_path: Path,
    summary_path: Path,
    *,
    failed_check: str,
    failure_message: str,
) -> tuple[bool, str]:
    """Persist a valid blocked Outcome, then derive its exact review report.

    The Outcome is the recovery fact.  Its report is deliberately derived only
    after the Outcome has been persisted, so report-generation failure cannot
    erase the usable blocked record.  The caller still fails closed when this
    function returns ``False``.
    """
    from ai_check_task_outcome import validate_outcome
    from ai_generate_task_outcome import generate_outcome
    from ai_render_task_outcome import render_task_outcome

    json_path, markdown_path = _outcome_paths(task)
    message = outcome_failure_message(failed_check, failure_message)
    try:
        payload = _pre_merge_outcome_input(task, contract_path, summary_path)
        evidence = dict(payload["evidence"])
        warnings = list(evidence.get("warnings", []))
        warnings.append(message)
        evidence["warnings"] = warnings
        evidence["status"] = "blocked"
        evidence["limitations"] = [
            *list(evidence.get("limitations", [])),
            {
                "sourceWarning": message,
                "title": "Finish verification is blocked",
                "affectedClaims": ["completion_claim", "archive_readiness"],
                "requiredEvidence": [f"a passing {failed_check} retry"],
                "forbiddenClaims": ["Do not claim this Work Item is complete or archive-ready."],
            },
        ]
        evidence["nonRiskExplanations"] = [
            *list(evidence.get("nonRiskExplanations", [])),
            {
                "sourceWarning": message,
                "reason": "The failed Finish gate is recorded as a recovery condition, not a completed result.",
                "evidence": [],
            },
        ]
        evidence["forbiddenClaims"] = [
            *list(evidence.get("forbiddenClaims", [])),
            "Do not claim a blocked Work Item has completed verification or may be archived.",
        ]
        outcome = generate_outcome(task, payload["bindings"], evidence=evidence)
        markdown = render_task_outcome(outcome)
        report = validate_outcome(outcome, markdown, expected_task_id=task)
        if not report.valid:
            return False, "; ".join(f"{item.code}: {item.message}" for item in report.errors)
        save_json(json_path, outcome)
        markdown_path.write_text(markdown, encoding="utf-8")
        _record_outcome_state(
            summary_path,
            {
                "status": "blocked",
                "jsonPath": json_path.relative_to(PROJECT_ROOT).as_posix(),
                "markdownPath": markdown_path.relative_to(PROJECT_ROOT).as_posix(),
                "rawEvidencePath": "derived:blocked_finish",
                "failedCheck": failed_check,
                "error": failure_message,
            },
        )
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return False, str(exc)

    report_ok, report_message = run_human_report_pipeline(task, summary_path)
    if not report_ok:
        return (
            False,
            f"blocked Outcome persisted but Human Benefit Report refresh failed: {report_message}",
        )
    return True, "blocked Outcome and Human Benefit Report persisted"


def outcome_failure_message(failed_check: str, failure_message: str) -> str:
    """Keep persisted blocked-Outcome text actionable and validator-safe.

    Detailed command output remains in the Summary verification record.  The
    Outcome is a human decision surface and deliberately carries only the gate
    identity and recovery direction when a tool error contains raw metrics.
    """
    normalized = " ".join(failure_message.split())
    if re.search(r"\b\d+(?:\.\d+)?\s*%", normalized):
        return (
            f"Finish blocked at {failed_check}: verification threshold was not met; "
            "inspect recorded verification output and rerun the gate."
        )
    return f"Finish blocked at {failed_check}: {normalized}"


def failed_check_from_summary(summary_path: Path, fallback: str) -> str:
    """Return the most recently recorded failed check without guessing success."""
    try:
        verification = load_json(summary_path).get("verification", [])
    except (OSError, ValueError, TypeError):
        return fallback
    if not isinstance(verification, list):
        return fallback
    for item in reversed(verification):
        if isinstance(item, dict) and item.get("result") == "failed":
            check = item.get("check")
            if isinstance(check, str) and check:
                return check
    return fallback


def documentation_alignment_issues(summary_path: Path, contract_data: dict[str, Any]) -> list[str]:
    """Return archive-required documentation-alignment defects without mutation.

    A completed Outcome is an archive prerequisite.  Revalidate the active
    Summary even when `--archive` reuses a prior Finish attestation because the
    Summary itself is intentionally excluded from that attestation's worktree
    digest to avoid a self-reference cycle.
    """
    from ai_check_summary import validate_documentation_alignment

    try:
        return validate_documentation_alignment(load_json(summary_path), contract_data)
    except (OSError, TypeError, ValueError) as exc:
        return [f"documentationAlignment could not be validated: {exc}"]


def return_blocked_finish_failure(
    *,
    task: str,
    contract_path: Path,
    summary_path: Path,
    failed_check: str,
    failure_message: str,
    code: int,
) -> int:
    """Fail closed while retaining the standard blocked recovery evidence."""
    blocked_ok, blocked_message = write_blocked_outcome(
        task,
        contract_path,
        summary_path,
        failed_check=failed_check,
        failure_message=failure_message,
    )
    if blocked_ok:
        print(f"Blocked Task Outcome persisted: {blocked_message}", file=sys.stderr)
    else:
        print(
            "ERROR: blocked Task Outcome/report recovery failed: " + blocked_message,
            file=sys.stderr,
        )
    return code if code else 1


def run_task_outcome_pipeline(
    task: str, summary_path: Path, contract_path: Path | None = None
) -> tuple[bool, str]:
    """Generate a mandatory pre-merge Outcome or validate explicit raw evidence."""
    summary = load_json(summary_path)
    input_value = summary.get("taskOutcomeInput")
    if not isinstance(input_value, str) or not input_value:
        if contract_path is None:
            return False, "mandatory Task Outcome requires the active Contract"
        json_path, markdown_path = _outcome_paths(task)
        ok, message = _write_and_validate_pre_merge_outcome(
            task, contract_path, summary_path, json_path, markdown_path
        )
        if not ok:
            _record_outcome_state(summary_path, {"status": "failed", "error": message})
            return False, message
        outcome = load_json(json_path)
        sections = outcome.get("sections", {})
        evidence_count = len(sections.get("evidence", [])) if isinstance(sections, dict) else 0
        _record_outcome_state(
            summary_path,
            {
                "status": outcome.get("status", "unknown"),
                "jsonPath": json_path.relative_to(PROJECT_ROOT).as_posix(),
                "markdownPath": markdown_path.relative_to(PROJECT_ROOT).as_posix(),
                "rawEvidencePath": "derived:pre_merge",
                "evidenceCount": evidence_count,
            },
        )
        return True, message
    input_path = PROJECT_ROOT / input_value
    json_path, markdown_path = _outcome_paths(task)
    if not input_path.exists():
        message = f"raw Evidence input does not exist: {input_value}"
        _record_outcome_state(
            summary_path, {"status": "failed", "rawEvidencePath": input_value, "error": message}
        )
        return False, message

    python = sys.executable
    commands = [
        [
            python,
            "scripts/ai_generate_task_outcome.py",
            input_value,
            str(json_path.relative_to(PROJECT_ROOT)),
            str(markdown_path.relative_to(PROJECT_ROOT)),
        ],
        [
            python,
            "-c",
            "from pathlib import Path; import sys; sys.path.insert(0, 'scripts'); from ai_check_task_outcome import validate_outcome; import json; outcome=json.loads(Path(sys.argv[1]).read_text()); report=validate_outcome(outcome, expected_task_id=sys.argv[3]); print('valid' if report.valid else '\\n'.join(f'{e.code}: {e.message}' for e in report.errors)); raise SystemExit(0 if report.valid else 1)",
            str(json_path.relative_to(PROJECT_ROOT)),
            str(markdown_path.relative_to(PROJECT_ROOT)),
            task,
        ],
        [
            python,
            "scripts/ai_render_task_outcome.py",
            str(json_path.relative_to(PROJECT_ROOT)),
            str(markdown_path.relative_to(PROJECT_ROOT)),
        ],
        [
            python,
            "-c",
            "from pathlib import Path; import sys; sys.path.insert(0, 'scripts'); from ai_check_task_outcome import validate_outcome; import json; outcome=json.loads(Path(sys.argv[1]).read_text()); report=validate_outcome(outcome, Path(sys.argv[2]).read_text(), expected_task_id=sys.argv[3]); print('valid' if report.valid else '\\n'.join(f'{e.code}: {e.message}' for e in report.errors)); raise SystemExit(0 if report.valid else 1)",
            str(json_path.relative_to(PROJECT_ROOT)),
            str(markdown_path.relative_to(PROJECT_ROOT)),
            task,
        ],
    ]
    for command in commands:
        code, _, output = run(command)
        if code != 0:
            message = " ".join((output or "Outcome pipeline command failed").split())[:500]
            _record_outcome_state(
                summary_path,
                {"status": "failed", "rawEvidencePath": input_value, "error": message},
            )
            return False, message
    outcome = json.loads(json_path.read_text(encoding="utf-8"))
    sections = outcome.get("sections", {})
    evidence_count = len(sections.get("evidence", [])) if isinstance(sections, dict) else 0
    _record_outcome_state(
        summary_path,
        {
            "status": outcome.get("status", "unknown"),
            "jsonPath": json_path.relative_to(PROJECT_ROOT).as_posix(),
            "markdownPath": markdown_path.relative_to(PROJECT_ROOT).as_posix(),
            "rawEvidencePath": input_value,
            "evidenceCount": evidence_count,
        },
    )
    return True, "Outcome pipeline passed"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AI Work Item finish checks.")
    parser.add_argument("--task", required=True)
    parser.add_argument(
        "--skip-quality", action="store_true", help="Skip the project quality gate."
    )
    parser.add_argument(
        "--archive",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Archive only after the agent has relayed the active Task Outcome to the human.",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Conversation language for the direct human report (en, zh-CN, or ja).",
    )
    return parser.parse_args()


def render_direct_outcome_report(outcome: dict[str, Any], language: str) -> str:
    """Render the active Outcome and the explicit archive boundary for the human."""
    from ai_render_task_outcome_multilingual import normalize_locale, render_localized_outcome

    locale = normalize_locale(language)
    heading, next_action = REPORT_BOUNDARY_TEXT[locale]
    return f"{heading}\n{render_localized_outcome(outcome, locale)}{next_action}\n"


def run_declared_checks(
    declared_items: list[dict[str, Any]],
    *,
    args: argparse.Namespace,
    contract: str,
    summary: str,
    contract_data: dict[str, Any],
    contract_path: Path,
    summary_path: Path,
    contract_hash: str,
    commit_sha: str,
    obs: Any,
) -> int:
    """Run declared checks and persist transactional verification evidence."""
    for item in declared_items:
        if not verification_key(item) or "command" in item:
            print(
                "ERROR: contractVersion 2 verification must use registered check IDs only",
                file=sys.stderr,
            )
            return 2
    transactional_markers_written = False
    outcome_requested = True
    for item in declared_items:
        check_id = verification_key(item)
        # These checks attest self-referential Summary/Status artifacts.  They
        # run together after ordinary verification has been recorded, where
        # each state write can be followed by a fresh Status projection.
        if check_id in STABILIZATION_CHECKS:
            continue
        if args.skip_quality and check_id == "quality":
            if item.get("required") is True:
                print(
                    "ERROR: --skip-quality cannot skip required Contract verification",
                    file=sys.stderr,
                )
                return 2
            continue
        try:
            cmd_str, command = render_check_command(
                check_id, contract_path=contract, summary_path=summary
            )
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        obs.check_started(check_id=check_id, command=cmd_str)
        # Outcome-enabled Summaries run aiSummary before Status. Pre-writing
        # pending markers for later self-referential checks would make aiSummary
        # reject its own Summary as incomplete; stabilization records them after
        # their real execution.
        if (
            not outcome_requested
            and not transactional_markers_written
            and verification_priority(item) >= 20
        ):
            current_digest = worktree_digest(changed_paths(contract_data))
            for candidate in declared_items:
                if verification_priority(candidate) >= 20:
                    candidate_id = verification_key(candidate)
                    candidate_command, _ = render_check_command(
                        candidate_id, contract_path=contract, summary_path=summary
                    )
                    record_result(
                        summary_path,
                        pending_evidence(
                            candidate_id,
                            candidate_command,
                            contract_hash=contract_hash,
                            commit_sha=commit_sha,
                            execution_contract_path=contract,
                            execution_summary_path=summary,
                            worktree_digest=current_digest,
                        ),
                    )
            transactional_markers_written = True
        if check_id == "aiSummary":
            current_digest = worktree_digest(changed_paths(contract_data))
            record_result(
                summary_path,
                evidence(
                    check_id,
                    cmd_str,
                    0,
                    0,
                    "pending transactional validation",
                    contract_hash=contract_hash,
                    commit_sha=commit_sha,
                    execution_contract_path=contract,
                    execution_summary_path=summary,
                    worktree_digest=current_digest,
                ),
            )
        code, duration, output = run(command)
        current_digest = worktree_digest(changed_paths(contract_data))
        record_result(
            summary_path,
            evidence(
                check_id,
                cmd_str,
                code,
                duration,
                output,
                contract_hash=contract_hash,
                commit_sha=commit_sha,
                execution_contract_path=contract,
                execution_summary_path=summary,
                worktree_digest=current_digest,
            ),
        )
        if code != 0 and item.get("required") is True:
            obs.check_failed(check_id=check_id, command=cmd_str, duration_ms=duration)
            return code
        if code == 0:
            obs.check_passed(check_id=check_id, command=cmd_str, duration_ms=duration)
        else:
            obs.check_failed(
                check_id=check_id,
                command=cmd_str,
                duration_ms=duration,
                detail="optional verification failed",
            )
    return 0


def _main_with_mutex(args: argparse.Namespace) -> int:
    contract, summary = task_paths(args.task)
    if not (PROJECT_ROOT / contract).exists():
        print(f"ERROR: Contract does not exist: {contract}", file=sys.stderr)
        return 1
    if not (PROJECT_ROOT / summary).exists():
        print(f"ERROR: Summary does not exist: {summary}", file=sys.stderr)
        return 1

    try:
        ensure_work_item_branch()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    contract_path = PROJECT_ROOT / contract
    summary_path = PROJECT_ROOT / summary
    contract_data = load_json(contract_path)
    if contract_data.get("contractVersion") != 2:
        print(
            "ERROR: ai-finish executes only contractVersion 2 check-ID Contracts", file=sys.stderr
        )
        return 2
    if (PROJECT_ROOT / "Makefile").exists():
        preflight_code, _, _ = run(["make", "ai-preflight", f"CONTRACT={contract}"])
        if preflight_code != 0:
            print(
                "ERROR: Work Item finish is blocked by the Human Decision Gate; "
                "record valid Decision Evidence and rerun Preflight until status is ready.",
                file=sys.stderr,
            )
            return return_blocked_finish_failure(
                task=args.task,
                contract_path=contract_path,
                summary_path=summary_path,
                failed_check="aiPreflight",
                failure_message="the Work Item preflight review is not ready",
                code=preflight_code,
            )
    contract_hash = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    commit_sha = current_head()
    from ai_check_agent_risk import validate_checkpoint_bindings

    checkpoint_issues = validate_checkpoint_bindings(
        contract_data,
        load_json(summary_path),
        expected_contract_hash=contract_hash,
    )
    if checkpoint_issues:
        for issue in checkpoint_issues:
            print(f"ERROR: {issue}", file=sys.stderr)
        print(
            checkpoint_recovery_guidance(checkpoint_issues, contract=contract, summary=summary),
            file=sys.stderr,
        )
        return return_blocked_finish_failure(
            task=args.task,
            contract_path=contract_path,
            summary_path=summary_path,
            failed_check="aiCheckpoint",
            failure_message="Contract/checkpoint binding is stale",
            code=2,
        )
    declared = contract_data.get("verification", [])
    if not isinstance(declared, list):
        print("ERROR: Contract verification must be a list", file=sys.stderr)
        return 1

    obs = create_observability(work_item_id=args.task)
    total_start = time.time()
    declared_items = inject_mandatory_verification_checks(
        [item for item in declared if isinstance(item, dict)]
    )
    summary_requests_outcome = True
    declared_items.sort(
        key=finish_execution_priority if summary_requests_outcome else verification_priority
    )
    ownership = preview(contract=contract_data)
    print("\n".join(format_preview(ownership)))
    ownership_failures = [
        item for item in ownership if item.state not in {"active_owned", "archived_owned"}
    ]
    if ownership_failures:
        print(
            "ERROR: finish is blocked until every task-era changed path has Work Item ownership.",
            file=sys.stderr,
        )
        return return_blocked_finish_failure(
            task=args.task,
            contract_path=contract_path,
            summary_path=summary_path,
            failed_check="aiDiffOwnership",
            failure_message="one or more task-era changed paths are unowned, ambiguous, restricted, or out of scope",
            code=1,
        )
    existing_summary = load_json(summary_path)
    reuse_archive_verification = args.archive and reusable_archive_verification(
        existing_summary,
        contract_data,
        contract_hash=contract_hash,
        commit_sha=commit_sha,
        contract=contract,
        summary_path=summary,
    )
    verification_start = time.time()
    code = 0
    if reuse_archive_verification:
        print("Reusing same-state ai-finish verification for archive")
    else:
        code = run_declared_checks(
            declared_items,
            args=args,
            contract=contract,
            summary=summary,
            contract_data=contract_data,
            contract_path=contract_path,
            summary_path=summary_path,
            contract_hash=contract_hash,
            commit_sha=commit_sha,
            obs=obs,
        )
    getattr(obs, "lifecycle_phase_finished", lambda *_args, **_kwargs: None)(
        "verification",
        duration_ms=elapsed_ms(verification_start),
        cache_outcome="hit" if reuse_archive_verification else "miss",
    )
    if code:
        obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
        return return_blocked_finish_failure(
            task=args.task,
            contract_path=contract_path,
            summary_path=summary_path,
            failed_check=failed_check_from_summary(summary_path, "verification"),
            failure_message="a required declared verification check failed",
            code=code,
        )

    alignment_issues = documentation_alignment_issues(summary_path, contract_data)
    if alignment_issues:
        obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
        return return_blocked_finish_failure(
            task=args.task,
            contract_path=contract_path,
            summary_path=summary_path,
            failed_check="documentationAlignment",
            failure_message="; ".join(alignment_issues[:3]),
            code=1,
        )

    if reuse_archive_verification:
        outcome_ok = _outcome_paths(args.task)[0].is_file()
        outcome_message = "existing outcome is bound by same-state verification"
        human_report_ok, human_report_message = outcome_ok, outcome_message
    else:
        outcome_ok, outcome_message = run_task_outcome_pipeline(
            contract_data["workItemId"], summary_path, contract_path
        )
        if outcome_ok:
            human_report_ok, human_report_message = run_human_report_pipeline(
                contract_data["workItemId"], summary_path
            )
        else:
            human_report_ok, human_report_message = False, outcome_message
    if not outcome_ok:
        print(f"ERROR: Task Outcome integration failed: {outcome_message}", file=sys.stderr)
        obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
        return return_blocked_finish_failure(
            task=args.task,
            contract_path=contract_path,
            summary_path=summary_path,
            failed_check="taskOutcome",
            failure_message=outcome_message,
            code=1,
        )
    if not human_report_ok:
        print(
            f"ERROR: Human Benefit Report integration failed: {human_report_message}",
            file=sys.stderr,
        )
        obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
        return return_blocked_finish_failure(
            task=args.task,
            contract_path=contract_path,
            summary_path=summary_path,
            failed_check="humanBenefitReport",
            failure_message=human_report_message,
            code=1,
        )

    # The Outcome/report pipeline expands the active Summary's declared
    # documentation surfaces. Recheck before any completed state is reported
    # or archive is invoked, rather than leaving archive as the first consumer
    # able to discover that the completion claim is stale.
    alignment_issues = documentation_alignment_issues(summary_path, contract_data)
    if alignment_issues:
        obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
        return return_blocked_finish_failure(
            task=args.task,
            contract_path=contract_path,
            summary_path=summary_path,
            failed_check="documentationAlignment",
            failure_message="; ".join(alignment_issues[:3]),
            code=1,
        )

    if reuse_archive_verification:
        print("Work Item finish checks reused from same-state evidence")
        outcome_json, _outcome_markdown = _outcome_paths(args.task)
        try:
            print(render_direct_outcome_report(load_json(outcome_json), args.language), end="")
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return return_blocked_finish_failure(
                task=args.task,
                contract_path=contract_path,
                summary_path=summary_path,
                failed_check="taskOutcomeReport",
                failure_message=str(exc),
                code=1,
            )
        if args.archive:
            code, output = run_pre_archive_critical_coverage(contract_data, obs=obs)
            if code != 0:
                obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
                return return_blocked_finish_failure(
                    task=args.task,
                    contract_path=contract_path,
                    summary_path=summary_path,
                    failed_check="preArchiveCriticalCoverage",
                    failure_message=output or "pre-archive critical coverage failed",
                    code=code,
                )
            archive_command = ["make", "archive-work-item", f"CONTRACT={contract}"]
            cmd_str = " ".join(archive_command)
            obs.check_started(check_id="archive-work-item", command=cmd_str)
            code, duration, _ = run(archive_command)
            if code != 0:
                obs.check_failed(
                    check_id="archive-work-item", command=cmd_str, duration_ms=duration
                )
                obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
                return return_blocked_finish_failure(
                    task=args.task,
                    contract_path=contract_path,
                    summary_path=summary_path,
                    failed_check="archive-work-item",
                    failure_message="archive command failed",
                    code=code,
                )
            obs.check_passed(check_id="archive-work-item", command=cmd_str, duration_ms=duration)
            report_ok, report_message = refresh_archived_human_report(args.task)
            if not report_ok:
                print(
                    f"ERROR: archived Human Benefit Report integration failed: {report_message}",
                    file=sys.stderr,
                )
                obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
                return return_blocked_finish_failure(
                    task=args.task,
                    contract_path=contract_path,
                    summary_path=summary_path,
                    failed_check="archivedHumanBenefitReport",
                    failure_message=report_message,
                    code=1,
                )
            print(archive_next_steps(args.task))
        obs.work_item_finished(result="passed", duration_ms=elapsed_ms(total_start))
        return 0

    # Establish a fail-closed readiness baseline before self-referential
    # stabilization. Positive readiness is persisted only after the first
    # stabilization and final Summary validation have passed.
    summary_data = load_json(summary_path)
    existing_readiness = summary_data.get("reviewReadiness")
    expected_focus = (
        existing_readiness.get("expectedReviewFocus", [])
        if isinstance(existing_readiness, dict)
        and isinstance(existing_readiness.get("expectedReviewFocus"), list)
        else []
    )
    summary_data["reviewReadiness"] = {
        "status": "not_ready",
        "reason": "Final stabilization and status checks are still pending.",
        "expectedReviewFocus": expected_focus,
    }
    save_json(summary_path, summary_data)

    # Summary/status are self-referential artifacts. Stabilize them after all
    # declared result evidence has been written, then attest without mutating.
    stabilization = [
        (
            "aiStatus",
            ["make", "generate-cockpit-status", f"CONTRACT={contract}", f"SUMMARY={summary}"],
        ),
        (
            "aiStatusCheck",
            ["make", "check-ai-status", f"CONTRACT={contract}", f"SUMMARY={summary}"],
        ),
        ("aiStatusConsistency", ["make", "check-ai-status-consistency"]),
        (
            "aiAgentRisk",
            ["make", "check-ai-agent-risk", f"CONTRACT={contract}", f"SUMMARY={summary}"],
        ),
        (
            "aiSummary",
            ["make", "check-ai-change-summary", f"SUMMARY={summary}", f"CONTRACT={contract}"],
        ),
    ]
    for check_id, command in stabilization:
        if check_id in {"aiStatusCheck", "aiStatusConsistency"}:
            refresh_command = [
                "make",
                "generate-cockpit-status",
                f"CONTRACT={contract}",
                f"SUMMARY={summary}",
            ]
            refresh_code, refresh_duration, _refresh_output = run(refresh_command)
            if refresh_code != 0:
                obs.check_failed(
                    check_id="aiStatus",
                    command=" ".join(refresh_command),
                    duration_ms=refresh_duration,
                )
                obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
                return return_blocked_finish_failure(
                    task=args.task,
                    contract_path=contract_path,
                    summary_path=summary_path,
                    failed_check="aiStatus",
                    failure_message="status refresh failed during stabilization",
                    code=refresh_code,
                )
        obs.check_started(check_id=check_id, command=" ".join(command))
        if check_id == "aiAgentRisk":
            code, duration, output = run(command, extra_env={"AI_FINISH_STABILIZING": "1"})
        else:
            code, duration, output = run(command)
        # Record actual result of stabilization check to Summary for debugging.
        current_worktree_digest = worktree_digest(changed_paths(contract_data))
        record_result(
            summary_path,
            evidence(
                check_id,
                " ".join(command),
                code,
                duration,
                output,
                contract_hash=contract_hash,
                commit_sha=commit_sha,
                execution_contract_path=contract,
                execution_summary_path=summary,
                worktree_digest=current_worktree_digest,
            ),
        )
        if code != 0:
            obs.check_failed(check_id=check_id, command=" ".join(command), duration_ms=duration)
            obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
            return return_blocked_finish_failure(
                task=args.task,
                contract_path=contract_path,
                summary_path=summary_path,
                failed_check=check_id,
                failure_message="stabilization check failed",
                code=code,
            )
        obs.check_passed(check_id=check_id, command=" ".join(command), duration_ms=duration)

    # Promote only after the declared checks, stabilization, and final Summary
    # validation have all passed. Promotion itself changes the Summary, so
    # status must be regenerated and checked once more against the promoted
    # state. These final checks intentionally do not mutate verification
    # evidence after the status has been generated.
    summary_data = load_json(summary_path)
    summary_data["reviewReadiness"] = promote_review_readiness(summary_data, contract_data)
    save_json(summary_path, summary_data)
    final_status_checks = [
        ["make", "generate-cockpit-status", f"CONTRACT={contract}", f"SUMMARY={summary}"],
        ["make", "check-ai-status", f"CONTRACT={contract}", f"SUMMARY={summary}"],
        ["make", "check-ai-status-consistency"],
    ]
    for command in final_status_checks:
        code, duration, output = run(command)
        if code != 0:
            failed_summary = load_json(summary_path)
            failed_summary["reviewReadiness"] = {
                "status": "not_ready",
                "reason": f"Final status validation failed: {' '.join(command)}",
                "expectedReviewFocus": expected_focus,
            }
            save_json(summary_path, failed_summary)
            print(output, file=sys.stderr)
            obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
            return return_blocked_finish_failure(
                task=args.task,
                contract_path=contract_path,
                summary_path=summary_path,
                failed_check="finalStatus",
                failure_message="final status validation failed",
                code=code,
            )

    # Revalidate the promoted Summary last and retain its evidence as the
    # archive's final worktree-digest anchor.
    summary_command = [
        "make",
        "check-ai-change-summary",
        f"SUMMARY={summary}",
        f"CONTRACT={contract}",
    ]
    code, duration, output = run(summary_command)
    if code != 0:
        failed_summary = load_json(summary_path)
        failed_summary["reviewReadiness"] = {
            "status": "not_ready",
            "reason": "Final Summary validation failed after Readiness promotion.",
            "expectedReviewFocus": expected_focus,
        }
        save_json(summary_path, failed_summary)
        print(output, file=sys.stderr)
        obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
        return return_blocked_finish_failure(
            task=args.task,
            contract_path=contract_path,
            summary_path=summary_path,
            failed_check="aiSummary",
            failure_message="final Summary validation failed",
            code=code,
        )
    record_result(
        summary_path,
        evidence(
            "aiSummary",
            " ".join(summary_command),
            code,
            duration,
            output,
            contract_hash=contract_hash,
            commit_sha=commit_sha,
            execution_contract_path=contract,
            execution_summary_path=summary,
            worktree_digest=worktree_digest_for_finish(changed_paths(contract_data), summary),
        ),
    )

    print("Work Item finish checks passed")
    record_fact_once(
        args.task,
        "finish_passed",
        {"contractPath": contract, "summaryPath": summary, "commitSha": commit_sha},
    )
    outcome_json, _outcome_markdown = _outcome_paths(args.task)
    try:
        print(render_direct_outcome_report(load_json(outcome_json), args.language), end="")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.archive:
        code, output = run_pre_archive_critical_coverage(contract_data, obs=obs)
        if code != 0:
            obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
            return return_blocked_finish_failure(
                task=args.task,
                contract_path=contract_path,
                summary_path=summary_path,
                failed_check="preArchiveCriticalCoverage",
                failure_message=output or "pre-archive critical coverage failed",
                code=code,
            )
        archive_command = ["make", "archive-work-item", f"CONTRACT={contract}"]
        cmd_str = " ".join(archive_command)
        obs.check_started(check_id="archive-work-item", command=cmd_str)
        code, duration, _ = run(archive_command)
        if code != 0:
            obs.check_failed(check_id="archive-work-item", command=cmd_str, duration_ms=duration)
            obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
            return code
        obs.check_passed(check_id="archive-work-item", command=cmd_str, duration_ms=duration)
        report_ok, report_message = refresh_archived_human_report(args.task)
        if not report_ok:
            print(
                f"ERROR: archived Human Benefit Report integration failed: {report_message}",
                file=sys.stderr,
            )
            obs.work_item_finished(result="failed", duration_ms=elapsed_ms(total_start))
            return 1
        print(archive_next_steps(args.task))
    duration_ms = elapsed_ms(total_start)
    getattr(obs, "lifecycle_phase_finished", lambda *_args, **_kwargs: None)(
        "finish", duration_ms=duration_ms, cache_outcome="miss"
    )
    obs.work_item_finished(result="passed", duration_ms=duration_ms)
    return 0


def main() -> int:
    args = parse_args()
    try:
        # Acquire before Preflight, verification, Outcome/report/status, or
        # archive paths can perform mutable lifecycle work.
        with finish_mutex(args.task, archive=args.archive):
            return _main_with_mutex(args)
    except FinishMutexError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
