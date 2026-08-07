"""Regression coverage for Dependabot intake without provider mutation."""

from __future__ import annotations

import hashlib

import pytest
from ai_check_dependabot_intake import decision, main
from ai_dependabot_intake import REQUIRED_EVIDENCE, assess


def candidate(number: int, path: str) -> dict[str, object]:
    return {
        "provider": "github",
        "author": "dependabot[bot]",
        "pullRequest": {
            "number": number,
            "url": f"https://github.com/example/repo/pull/{number}",
            "head": "a" * 40,
        },
        "changedPaths": [path],
        "diffDigest": hashlib.sha256(path.encode()).hexdigest(),
    }


def test_pip_and_action_candidates_fail_closed_without_archived_successor() -> None:
    for item in (
        candidate(639, "requirements-dev.in"),
        candidate(640, ".github/workflows/smoke.yml"),
    ):
        result = assess(item)
        assert result["state"] == "blocked"
        assert result["requiredEvidence"] == REQUIRED_EVIDENCE
        assert result["automaticMergeAuthorized"] is False


def test_exact_archived_successor_binding_is_eligible_but_not_auto_merge() -> None:
    item = candidate(639, "requirements-dev.in")
    binding = {
        "pullRequestUrl": item["pullRequest"]["url"],
        "head": item["pullRequest"]["head"],
        "diffDigest": item["diffDigest"],
    }
    result = assess(
        item,
        {
            "base": "current-main",
            "workItemId": "ruff-update",
            "branch": "codex/ruff-update",
            "contract": "archived",
            "startReceipt": "archived",
            "summary": "archived",
            "outcome": "archived",
            "archiveManifest": "archived",
            "source": binding,
        },
    )
    assert result["state"] == "eligible_for_current_main_successor"
    assert result["automaticMergeAuthorized"] is False


def test_hosted_gate_rejects_raw_bot_but_leaves_ordinary_prs_to_existing_lifecycle() -> None:
    assert (
        decision("pull_request", "dependabot[bot]", "https://example/pull/639", "a" * 40)["state"]
        == "blocked"
    )
    assert decision("pull_request", "RayIori", "", "")["state"] == "not_applicable"


def test_hosted_gate_cli_exits_nonzero_for_raw_bot_and_zero_for_human(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "ai_check_dependabot_intake.py",
            "--event-name",
            "pull_request",
            "--author",
            "dependabot[bot]",
            "--pull-request-url",
            "https://example/pull/639",
            "--head",
            "a" * 40,
        ],
    )
    assert main() == 1
    assert '"state": "blocked"' in capsys.readouterr().out

    monkeypatch.setattr(
        "sys.argv",
        [
            "ai_check_dependabot_intake.py",
            "--event-name",
            "pull_request",
            "--author",
            "RayIori",
        ],
    )
    assert main() == 0
    assert '"state": "not_applicable"' in capsys.readouterr().out
