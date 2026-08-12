import hashlib
import json
from types import SimpleNamespace

import ai_post_archive_recovery as recovery
import pytest


def write_archive(root, task="example-task"):
    archive = root / ".ai/work-items/archive/2026"
    archive.mkdir(parents=True)
    files = {
        f"{task}.contract.json": {"workItemId": task},
        f"{task}.summary.json": {"workItemId": task},
        f"{task}.outcome.json": {"workItemId": task, "status": "completed"},
        f"{task}.archive-manifest.json": {"workItemId": task},
    }
    for name, value in files.items():
        (archive / name).write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return archive


def test_open_recovery_binds_failed_pr_audit_without_mutating_archive(tmp_path):
    archive = write_archive(tmp_path)
    original = {path.name: path.read_bytes() for path in archive.iterdir()}

    receipt = recovery.open_post_archive_recovery(
        root=tmp_path,
        task="example-task",
        base_commit="a" * 40,
        issue="https://github.com/example/repo/issues/1",
        authority="user-authorized same Work Item recovery",
        recovery_paths=["scripts/ai_finish.py", "tests/test_finish.py"],
        run_pr_audit=lambda _command: (1, "changed-critical coverage failed: below floor"),
        worktree_clean=lambda: True,
    )

    assert receipt["failure"]["gate"] == "changedCriticalCoverage"
    assert receipt["recoveryPaths"] == ["scripts/ai_finish.py", "tests/test_finish.py"]
    assert (
        receipt["archive"]["outcome"]["sha256"]
        == hashlib.sha256(original["example-task.outcome.json"]).hexdigest()
    )
    assert {path.name: path.read_bytes() for path in archive.iterdir()} == original
    assert recovery.validate_recovery_receipt(tmp_path, receipt, pr_base="a" * 40) == []


def test_open_recovery_refuses_when_pr_audit_is_not_failing(tmp_path):
    write_archive(tmp_path)

    with pytest.raises(ValueError, match="must fail"):
        recovery.open_post_archive_recovery(
            root=tmp_path,
            task="example-task",
            base_commit="a" * 40,
            issue="https://github.com/example/repo/issues/1",
            authority="user-authorized same Work Item recovery",
            recovery_paths=["scripts/ai_finish.py"],
            run_pr_audit=lambda _command: (0, "aggregate PR check passed"),
            worktree_clean=lambda: True,
        )


def hosted_provider(endpoint: str) -> bytes:
    responses = {
        "/repos/spirex-ds-dev/ai-cockpit-template/actions/runs/42": {
            "id": 42,
            "event": "pull_request",
            "head_sha": "b" * 40,
            "status": "completed",
            "conclusion": "failure",
            "path": ".github/workflows/smoke.yml",
            "html_url": "https://github.com/spirex-ds-dev/ai-cockpit-template/actions/runs/42",
            "pull_requests": [{"number": 716}],
        },
        "/repos/spirex-ds-dev/ai-cockpit-template/actions/jobs/84": {
            "id": 84,
            "run_id": 42,
            "name": "template-smoke",
            "status": "completed",
            "conclusion": "failure",
        },
    }
    if endpoint.endswith("/logs"):
        return (
            b"2085 passed, 3 warnings in 560.75s (0:09:20)\n"
            b"FAIL Required test coverage of 85.1% not reached. Total coverage: 85.09%\n"
        )
    return json.dumps(responses[endpoint]).encode()


def test_open_hosted_recovery_binds_exact_failed_provider_coverage_evidence(tmp_path):
    write_archive(tmp_path)

    receipt = recovery.open_hosted_post_archive_recovery(
        root=tmp_path,
        task="example-task",
        base_commit="a" * 40,
        issue="https://github.com/spirex-ds-dev/ai-cockpit-template/issues/709",
        authority="user-authorized same Work Item recovery",
        recovery_paths=["tests/test_resume.py"],
        repository="spirex-ds-dev/ai-cockpit-template",
        pull_request=716,
        failed_candidate_head="b" * 40,
        run_id=42,
        job_id=84,
        fetch_provider=hosted_provider,
        worktree_clean=lambda: True,
    )

    assert receipt["failure"]["gate"] == "hostedAggregateCoverage"
    assert receipt["provider"]["runId"] == 42
    assert receipt["provider"]["jobId"] == 84
    assert receipt["provider"]["observedCoverage"] == {
        "actual": 85.09,
        "required": 85.1,
        "parserVersion": 1,
    }
    assert (
        recovery.validate_recovery_receipt(
            tmp_path, receipt, pr_base="a" * 40, fetch_provider=hosted_provider
        )
        == []
    )


def test_hosted_receipt_validation_is_offline_after_creation(tmp_path):
    write_archive(tmp_path)
    receipt = recovery.open_hosted_post_archive_recovery(
        root=tmp_path,
        task="example-task",
        base_commit="a" * 40,
        issue="https://github.com/spirex-ds-dev/ai-cockpit-template/issues/709",
        authority="user-authorized same Work Item recovery",
        recovery_paths=["tests/test_resume.py"],
        repository="spirex-ds-dev/ai-cockpit-template",
        pull_request=716,
        failed_candidate_head="b" * 40,
        run_id=42,
        job_id=84,
        fetch_provider=hosted_provider,
        worktree_clean=lambda: True,
    )

    def provider_must_not_be_called(_endpoint):
        pytest.fail("validation must use the provider facts captured when the receipt was created")

    assert (
        recovery.validate_recovery_receipt(
            tmp_path, receipt, pr_base="a" * 40, fetch_provider=provider_must_not_be_called
        )
        == []
    )


def test_hosted_receipt_validation_rejects_an_incoherent_recorded_run_url(tmp_path):
    write_archive(tmp_path)
    receipt = recovery.open_hosted_post_archive_recovery(
        root=tmp_path,
        task="example-task",
        base_commit="a" * 40,
        issue="https://github.com/spirex-ds-dev/ai-cockpit-template/issues/709",
        authority="user-authorized same Work Item recovery",
        recovery_paths=["tests/test_resume.py"],
        repository="spirex-ds-dev/ai-cockpit-template",
        pull_request=716,
        failed_candidate_head="b" * 40,
        run_id=42,
        job_id=84,
        fetch_provider=hosted_provider,
        worktree_clean=lambda: True,
    )
    receipt["provider"]["runUrl"] = "https://github.com/other/repository/actions/runs/42"

    assert recovery.validate_recovery_receipt(tmp_path, receipt, pr_base="a" * 40) == [
        "recorded provider run URL does not match its repository and run ID"
    ]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda provider: provider.update(kind="other"),
            "recorded provider kind is not github_actions",
        ),
        (
            lambda provider: provider.update(event="push"),
            "recorded provider event is not pull_request",
        ),
        (
            lambda provider: provider.update(runStatus="queued"),
            "recorded provider run is not a completed failure",
        ),
        (
            lambda provider: provider.update(jobConclusion="success"),
            "recorded provider job is not a failure",
        ),
        (
            lambda provider: provider.update(logSha256="invalid"),
            "recorded provider log digest is invalid",
        ),
        (
            lambda provider: provider["observedCoverage"].update(actual=85.1),
            "recorded provider coverage does not prove a below-floor failure",
        ),
    ],
)
def test_hosted_coverage_receipt_validation_rejects_incoherent_recorded_facts(
    tmp_path, mutate, message
):
    write_archive(tmp_path)
    receipt = recovery.open_hosted_post_archive_recovery(
        root=tmp_path,
        task="example-task",
        base_commit="a" * 40,
        issue="https://github.com/spirex-ds-dev/ai-cockpit-template/issues/709",
        authority="user-authorized same Work Item recovery",
        recovery_paths=["tests/test_resume.py"],
        repository="spirex-ds-dev/ai-cockpit-template",
        pull_request=716,
        failed_candidate_head="b" * 40,
        run_id=42,
        job_id=84,
        fetch_provider=hosted_provider,
        worktree_clean=lambda: True,
    )
    mutate(receipt["provider"])

    assert recovery.validate_recovery_receipt(tmp_path, receipt, pr_base="a" * 40) == [message]


def functional_failure_provider(endpoint: str) -> bytes:
    responses = {
        "/repos/spirex-ds-dev/ai-cockpit-template/actions/runs/43": {
            "id": 43,
            "event": "pull_request",
            "head_sha": "c" * 40,
            "status": "completed",
            "conclusion": "failure",
            "path": ".github/workflows/compatibility.yml",
            "html_url": "https://github.com/spirex-ds-dev/ai-cockpit-template/actions/runs/43",
            "pull_requests": [{"number": 765}],
        },
        "/repos/spirex-ds-dev/ai-cockpit-template/actions/jobs/85": {
            "id": 85,
            "run_id": 43,
            "name": "extended-real-stack-quality (java)",
            "status": "completed",
            "conclusion": "failure",
        },
    }
    if endpoint.endswith("/logs"):
        return (
            b"BLOCKED: required Java major is missing for lane 'default'. Recovery: configure it.\n"
        )
    return json.dumps(responses[endpoint]).encode()


def pytest_functional_failure_provider(endpoint: str) -> bytes:
    if endpoint.endswith("/logs"):
        return (
            b"=========================== short test summary info ============================\n"
            b"FAILED tests/test_capability_truth_matrix.py::test_machine_matrix_evidence_binding_is_valid\n"
            b"FAILED tests/test_absurd_capability_truth.py::test_capability_matrix_has_bound_evidence\n"
            b"=================== 2 failed, 591 passed, 2 warnings in 93.29s ===================\n"
        )
    return functional_failure_provider(endpoint)


def test_hosted_functional_recovery_accepts_canonical_pytest_failure():
    provider = recovery.verified_hosted_functional_failure(
        repository="spirex-ds-dev/ai-cockpit-template",
        pull_request=765,
        failed_candidate_head="c" * 40,
        run_id=43,
        job_id=85,
        fetch_provider=pytest_functional_failure_provider,
    )

    assert provider["failureMarker"] == "pytest_failure"


def second_functional_failure_provider(endpoint: str) -> bytes:
    responses = {
        "/repos/spirex-ds-dev/ai-cockpit-template/actions/runs/44": {
            "id": 44,
            "event": "pull_request",
            "head_sha": "d" * 40,
            "status": "completed",
            "conclusion": "failure",
            "path": ".github/workflows/smoke.yml",
            "html_url": "https://github.com/spirex-ds-dev/ai-cockpit-template/actions/runs/44",
            "pull_requests": [{"number": 765}],
        },
        "/repos/spirex-ds-dev/ai-cockpit-template/actions/jobs/86": {
            "id": 86,
            "run_id": 44,
            "name": "template-smoke",
            "status": "completed",
            "conclusion": "failure",
        },
    }
    if endpoint.endswith("/logs"):
        return b"BLOCKED: provider-bound recovery audit lacks token. Recovery: provide a token.\n"
    return json.dumps(responses[endpoint]).encode()


def test_github_api_prefers_terminal_safe_gh_output_when_supported(monkeypatch):
    observed = {}

    def fake_run(args, **kwargs):
        observed["args"] = args
        observed["env"] = kwargs["env"]
        return SimpleNamespace(returncode=0, stdout=b"{}", stderr=b"")

    monkeypatch.setattr(recovery.subprocess, "run", fake_run)

    assert recovery._github_api("/repos/spirex-ds-dev/ai-cockpit-template") == b"{}"
    assert observed["args"] == [
        "gh",
        "api",
        "--allow-escape-sequences",
        "/repos/spirex-ds-dev/ai-cockpit-template",
    ]


def test_github_api_retries_without_terminal_flag_for_older_runners(monkeypatch):
    calls = []

    def fake_run(args, **_kwargs):
        calls.append(args)
        if len(calls) == 1:
            return SimpleNamespace(
                returncode=1, stdout=b"", stderr=b"unknown flag: --allow-escape-sequences"
            )
        return SimpleNamespace(returncode=0, stdout=b"{}", stderr=b"")

    monkeypatch.setattr(recovery.subprocess, "run", fake_run)

    assert recovery._github_api("/repos/spirex-ds-dev/ai-cockpit-template") == b"{}"
    assert calls == [
        ["gh", "api", "--allow-escape-sequences", "/repos/spirex-ds-dev/ai-cockpit-template"],
        ["gh", "api", "/repos/spirex-ds-dev/ai-cockpit-template"],
    ]


def test_open_hosted_recovery_binds_exact_functional_failure_evidence(tmp_path):
    write_archive(tmp_path)

    receipt = recovery.open_hosted_functional_failure_recovery(
        root=tmp_path,
        task="example-task",
        base_commit="a" * 40,
        issue="https://github.com/spirex-ds-dev/ai-cockpit-template/issues/620",
        authority="user-authorized same Work Item recovery",
        recovery_paths=[".github/workflows/compatibility.yml"],
        repository="spirex-ds-dev/ai-cockpit-template",
        pull_request=765,
        failed_candidate_head="c" * 40,
        run_id=43,
        job_id=85,
        fetch_provider=functional_failure_provider,
        worktree_clean=lambda: True,
    )

    assert receipt["failure"]["gate"] == "hostedFunctionalFailure"
    assert receipt["provider"]["jobName"] == "extended-real-stack-quality (java)"
    assert (
        recovery.validate_recovery_receipt(
            tmp_path, receipt, pr_base="a" * 40, fetch_provider=functional_failure_provider
        )
        == []
    )


def test_hosted_functional_recovery_appends_a_distinct_receipt_for_the_same_work_item(tmp_path):
    write_archive(tmp_path)
    common = {
        "root": tmp_path,
        "task": "example-task",
        "base_commit": "a" * 40,
        "issue": "https://github.com/spirex-ds-dev/ai-cockpit-template/issues/620",
        "authority": "user-authorized same Work Item recovery",
        "repository": "spirex-ds-dev/ai-cockpit-template",
        "pull_request": 765,
        "worktree_clean": lambda: True,
    }
    recovery.open_hosted_functional_failure_recovery(
        **common,
        recovery_paths=[".github/workflows/compatibility.yml"],
        failed_candidate_head="c" * 40,
        run_id=43,
        job_id=85,
        fetch_provider=functional_failure_provider,
    )

    receipt = recovery.open_hosted_functional_failure_recovery(
        **common,
        recovery_paths=[".github/workflows/smoke.yml"],
        failed_candidate_head="d" * 40,
        run_id=44,
        job_id=86,
        fetch_provider=second_functional_failure_provider,
    )

    receipts = tmp_path / ".ai/work-items/recovery-receipts"
    assert receipt["provider"]["runId"] == 44
    assert sorted(path.name for path in receipts.glob("*.json")) == [
        "example-task-44-86.json",
        "example-task.json",
    ]


@pytest.mark.parametrize(
    ("repository", "provider", "message"),
    [
        ("not a repository", functional_failure_provider, "owner/name"),
        (
            "spirex-ds-dev/ai-cockpit-template",
            lambda endpoint: (
                b"not a governed failure"
                if endpoint.endswith("/logs")
                else functional_failure_provider(endpoint)
            ),
            "canonical fail-closed functional failure",
        ),
        (
            "spirex-ds-dev/ai-cockpit-template",
            lambda endpoint: (
                functional_failure_provider(endpoint).replace(
                    b'"name": "extended-real-stack-quality (java)"', b'"name": ""'
                )
                if endpoint.endswith("/85")
                else functional_failure_provider(endpoint)
            ),
            "job name",
        ),
    ],
)
def test_hosted_functional_recovery_rejects_unbound_provider_facts(repository, provider, message):
    with pytest.raises(ValueError, match=message):
        recovery.verified_hosted_functional_failure(
            repository=repository,
            pull_request=765,
            failed_candidate_head="c" * 40,
            run_id=43,
            job_id=85,
            fetch_provider=provider,
        )


def test_open_hosted_recovery_rejects_a_stale_provider_head(tmp_path):
    write_archive(tmp_path)

    with pytest.raises(ValueError, match="Head SHA"):
        recovery.open_hosted_post_archive_recovery(
            root=tmp_path,
            task="example-task",
            base_commit="a" * 40,
            issue="https://github.com/spirex-ds-dev/ai-cockpit-template/issues/709",
            authority="user-authorized same Work Item recovery",
            recovery_paths=["tests/test_resume.py"],
            repository="spirex-ds-dev/ai-cockpit-template",
            pull_request=716,
            failed_candidate_head="c" * 40,
            run_id=42,
            job_id=84,
            fetch_provider=hosted_provider,
            worktree_clean=lambda: True,
        )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda endpoint, payload: (
                payload.replace(b'"number": 716', b'"number": 999')
                if endpoint.endswith("/42")
                else payload
            ),
            "pull request",
        ),
        (
            lambda endpoint, payload: (
                payload.replace(b'"name": "template-smoke"', b'"name": "other"')
                if endpoint.endswith("/84")
                else payload
            ),
            "template-smoke",
        ),
        (
            lambda endpoint, payload: (
                b"project-test failed" if endpoint.endswith("/logs") else payload
            ),
            "canonical coverage failure",
        ),
    ],
)
def test_hosted_recovery_rejects_unbound_provider_facts(mutate, message):
    def provider(endpoint):
        return mutate(endpoint, hosted_provider(endpoint))

    with pytest.raises(ValueError, match=message):
        recovery.verified_hosted_coverage_failure(
            repository="spirex-ds-dev/ai-cockpit-template",
            pull_request=716,
            failed_candidate_head="b" * 40,
            run_id=42,
            job_id=84,
            fetch_provider=provider,
        )


def test_hosted_recovery_rejects_provider_unavailability():
    def unavailable(_endpoint):
        raise OSError("network unavailable")

    with pytest.raises(ValueError, match="provider response is invalid"):
        recovery.verified_hosted_coverage_failure(
            repository="spirex-ds-dev/ai-cockpit-template",
            pull_request=716,
            failed_candidate_head="b" * 40,
            run_id=42,
            job_id=84,
            fetch_provider=unavailable,
        )


def test_github_provider_log_reader_uses_terminal_safe_gh_api_invocation(monkeypatch):
    captured = {}

    def run(command, **_kwargs):
        captured["command"] = command
        return type("Result", (), {"returncode": 0, "stdout": b"log", "stderr": b""})()

    monkeypatch.setattr(recovery.subprocess, "run", run)

    assert recovery._github_api("/repos/o/r/actions/jobs/1/logs") == b"log"
    assert captured["command"] == [
        "gh",
        "api",
        "--allow-escape-sequences",
        "/repos/o/r/actions/jobs/1/logs",
    ]
