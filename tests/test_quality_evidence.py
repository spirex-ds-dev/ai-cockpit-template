from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest
import quality_evidence
import quality_session_lock


def _state(tmp_path: Path) -> dict[str, object]:
    return {
        "baseCommit": "a" * 40,
        "treeDigest": "sha256:tree",
        "changedPathsDigest": "sha256:paths",
        "environmentDigest": "sha256:environment",
        "profile": "strict",
        "sessionId": "session-1",
        "summaryDigest": "sha256:summary",
    }


def test_reusable_full_receipt_accepts_only_exact_passing_state(tmp_path):
    receipt = quality_evidence.build_receipt(_state(tmp_path))
    assert quality_evidence.validate_receipt(receipt, _state(tmp_path), stage="task") == []


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("baseCommit", "b" * 40),
        ("treeDigest", "sha256:other-tree"),
        ("changedPathsDigest", "sha256:other-paths"),
        ("environmentDigest", "sha256:other-environment"),
        ("profile", "standard"),
        ("summaryDigest", "sha256:other-summary"),
    ],
)
def test_reusable_full_receipt_rejects_every_binding_mismatch(tmp_path, field, replacement):
    receipt = quality_evidence.build_receipt(_state(tmp_path))
    requested = _state(tmp_path)
    requested[field] = replacement

    assert field in " ".join(quality_evidence.validate_receipt(receipt, requested, stage="task"))


@pytest.mark.parametrize("stage", ["merge", "convergence", "release"])
def test_reusable_full_receipt_is_forbidden_at_final_stages(tmp_path, stage):
    receipt = quality_evidence.build_receipt(_state(tmp_path))

    assert quality_evidence.validate_receipt(receipt, _state(tmp_path), stage=stage) == [
        f"reusable local Full quality evidence is forbidden for {stage}; run fresh quality"
    ]


def test_receipt_file_rejects_malformed_or_non_passing_summary(tmp_path):
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text("not json", encoding="utf-8")
    with pytest.raises((ValueError, TypeError), match="invalid reusable quality receipt"):
        quality_evidence.load_receipt(receipt_path)

    receipt = quality_evidence.build_receipt(_state(tmp_path))
    receipt["summaryDecision"] = "FAIL"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "summaryDecision" in " ".join(
        quality_evidence.validate_receipt(
            quality_evidence.load_receipt(receipt_path), _state(tmp_path), stage="task"
        )
    )


def test_reuse_is_rejected_while_a_quality_session_is_active(tmp_path):
    lock_path = tmp_path / "target" / "quality" / "session.lock"
    with quality_session_lock.acquire(lock_path, worktree=tmp_path):
        assert quality_evidence.active_lock(lock_path) is True
    assert quality_evidence.active_lock(lock_path) is False


def test_quality_state_and_capture_bind_real_changed_paths_and_environment(tmp_path):
    (tmp_path / "Makefile").write_text("all:\n", encoding="utf-8")
    (tmp_path / "tracked.txt").write_text("state\n", encoding="utf-8")
    session = tmp_path / "target/quality/sessions/session-1"
    session.mkdir(parents=True)
    (session / "summary.json").write_text('{"decision":"PASS"}', encoding="utf-8")

    def fake_git(_root, *args):
        if args[:2] == ("rev-parse", "HEAD"):
            return "head\n"
        if args[0] == "ls-files":
            return "target/ignored\ntracked.txt\n"
        return ""

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(quality_evidence, "git", fake_git)
    try:
        state = quality_evidence.quality_state(
            tmp_path, base="base", session_root=session, profile="strict"
        )
        output = tmp_path / "receipt.json"
        assert (
            quality_evidence.capture(
                Namespace(
                    root=tmp_path,
                    base="base",
                    session_root=session,
                    profile="strict",
                    output=output,
                )
            )
            == 0
        )
    finally:
        monkeypatch.undo()

    assert state["baseCommit"] == "base"
    assert (
        quality_evidence.load_receipt(output)["changedPathsDigest"] == state["changedPathsDigest"]
    )


def test_git_and_quality_state_fail_closed_for_command_or_summary_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(
        quality_evidence.subprocess,
        "run",
        lambda *_args, **_kwargs: Namespace(returncode=1, stderr="bad git", stdout=""),
    )
    with pytest.raises(ValueError, match="bad git"):
        quality_evidence.git(tmp_path, "status")
    monkeypatch.setattr(quality_evidence, "tracked_and_untracked_paths", lambda *_args: [])
    session = tmp_path / "session"
    session.mkdir()
    with pytest.raises(ValueError, match="missing Full"):
        quality_evidence.quality_state(
            tmp_path, base="HEAD", session_root=session, profile="strict"
        )
    (session / "summary.json").write_text('{"decision":"FAIL"}', encoding="utf-8")
    with pytest.raises(ValueError, match="not PASS"):
        quality_evidence.quality_state(
            tmp_path, base="HEAD", session_root=session, profile="strict"
        )


def test_validate_cli_rejects_active_lock_invalid_session_and_receipt_mismatch(
    tmp_path, monkeypatch, capsys
):
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(
        json.dumps(quality_evidence.build_receipt(_state(tmp_path))), encoding="utf-8"
    )
    args = Namespace(root=tmp_path, base=None, receipt=receipt_path, stage="task")
    monkeypatch.setattr(quality_evidence, "active_lock", lambda _path: True)
    assert quality_evidence.validate(args) == 1
    assert "session is active" in capsys.readouterr().err

    monkeypatch.setattr(quality_evidence, "active_lock", lambda _path: False)
    receipt_path.write_text(json.dumps({"sessionId": ""}), encoding="utf-8")
    assert quality_evidence.validate(args) == 1
    assert "sessionId is invalid" in capsys.readouterr().err

    receipt_path.write_text(
        json.dumps(quality_evidence.build_receipt(_state(tmp_path))), encoding="utf-8"
    )
    monkeypatch.setattr(
        quality_evidence, "quality_state", lambda *_args, **_kwargs: _state(tmp_path)
    )
    assert quality_evidence.validate(args) == 0
    assert "valid for task only" in capsys.readouterr().out


def test_validate_cli_rejects_final_stage_before_loading_receipt(tmp_path, capsys):
    args = Namespace(root=tmp_path, base=None, receipt=tmp_path / "missing.json", stage="release")
    assert quality_evidence.validate(args) == 1
    assert "forbidden for release" in capsys.readouterr().err


def test_cli_parsing_main_and_invalid_receipt_types(tmp_path, monkeypatch, capsys):
    receipt = tmp_path / "receipt.json"
    receipt.write_text("[]", encoding="utf-8")
    with pytest.raises(TypeError, match="object required"):
        quality_evidence.load_receipt(receipt)
    monkeypatch.setattr(
        "sys.argv",
        [
            "quality_evidence.py",
            "--root",
            str(tmp_path),
            "capture",
            "--session-root",
            str(tmp_path / "session"),
            "--profile",
            "strict",
            "--output",
            str(receipt),
        ],
    )
    parsed = quality_evidence.parse_args()
    assert parsed.command == "capture" and parsed.profile == "strict"
    monkeypatch.setattr(quality_evidence, "capture", lambda _args: 0)
    assert quality_evidence.main() == 0
    monkeypatch.setattr(
        quality_evidence, "capture", lambda _args: (_ for _ in ()).throw(ValueError("bad"))
    )
    assert quality_evidence.main() == 1
    assert "invalid: bad" in capsys.readouterr().err
