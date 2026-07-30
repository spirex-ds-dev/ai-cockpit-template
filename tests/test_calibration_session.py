import json
import subprocess
import sys
from pathlib import Path

import ai_calibrate
import pytest
from ai_calibrate import (
    CALIBRATION_STAGES,
    CalibrationError,
    CalibrationSession,
    load_session,
    persist_activation,
)


def complete(session: CalibrationSession) -> None:
    for stage in CALIBRATION_STAGES:
        session.answer(stage, "Y", answer_type="yes_no")


def record_complete_evidence(session: CalibrationSession) -> None:
    for stage in CALIBRATION_STAGES:
        session.record_checklist_evidence(
            stage,
            observed_evidence=[f"evidence/{stage}.txt"],
            candidate_change=f"no change: {stage} is evidenced",
            owner="repository-owner",
            reviewer="repository-reviewer",
            decision="PASS",
            decision_reason=f"{stage} evidence is complete",
            retry_step="",
        )


def complete_candidate(session: CalibrationSession) -> dict[str, object]:
    complete(session)
    record_complete_evidence(session)
    assert session.review()["status"] == "ready"
    assert session.full_self_check()["status"] == "passed"
    assert session.governance_simulation()["status"] == "passed"
    return session.prepare_candidate()


def confirm_candidate(session: CalibrationSession, candidate: dict[str, object]) -> None:
    for phase in ("reviewer", "owner"):
        session.confirm(
            phase,
            candidate_revision=int(candidate["revision"]),
            candidate_digest=str(candidate["digest"]),
        )


def evidence_cli_args(stage: str) -> tuple[str, ...]:
    return (
        "--stage",
        stage,
        "--observed-evidence",
        f"evidence/{stage}.txt",
        "--candidate-change",
        f"no change: {stage} is evidenced",
        "--owner",
        "repository-owner",
        "--reviewer",
        "repository-reviewer",
        "--decision",
        "PASS",
        "--decision-reason",
        f"{stage} evidence is complete",
    )


def test_all_unknown_answers_block_core_readiness_and_candidate_preparation():
    session = CalibrationSession.start("all-unknown")
    for stage in CALIBRATION_STAGES:
        session.answer(stage, "Unknown", answer_type="unknown")
        session.record_checklist_evidence(
            stage,
            observed_evidence=[f"evidence/{stage}.txt"],
            candidate_change="no change: evidence remains unknown",
            owner="repository-owner",
            reviewer="repository-reviewer",
            decision="STOP",
            decision_reason="Required fact is Unknown",
            retry_step="Obtain repository evidence and answer again",
        )

    assert {stage["status"] for stage in session.data["stages"]} == {"blocked"}
    assert session.review()["status"] == "blocked"
    assert session.full_self_check()["status"] == "blocked"
    assert session.governance_simulation()["status"] == "blocked"
    with pytest.raises(CalibrationError, match="blocking calibration evidence"):
        session.prepare_candidate()


def test_candidate_requires_complete_structured_checklist_evidence():
    session = CalibrationSession.start("evidence-required")
    complete(session)

    review = session.review()
    assert review["status"] == "blocked"
    assert review["blockingFields"][CALIBRATION_STAGES[0]] == [
        "candidateChange",
        "decision",
        "decisionReason",
        "observedEvidence",
        "owner",
        "reviewer",
    ]
    with pytest.raises(CalibrationError, match="blocking calibration evidence"):
        session.prepare_candidate()

    record_complete_evidence(session)
    assert session.review()["status"] == "ready"


def test_confirmation_binds_candidate_revision_and_digest_and_mutation_invalidates():
    session = CalibrationSession.start("candidate-binding")
    candidate = complete_candidate(session)

    with pytest.raises(CalibrationError, match="Candidate revision"):
        session.confirm(
            "reviewer",
            candidate_revision=int(candidate["revision"]) + 1,
            candidate_digest=str(candidate["digest"]),
        )
    with pytest.raises(CalibrationError, match="Candidate digest"):
        session.confirm(
            "reviewer",
            candidate_revision=int(candidate["revision"]),
            candidate_digest="0" * 64,
        )
    assert session.data["confirmations"] == {}

    confirm_candidate(session, candidate)
    assert {record["candidateDigest"] for record in session.data["confirmations"].values()} == {
        candidate["digest"]
    }

    session.answer(CALIBRATION_STAGES[0], "N", answer_type="yes_no")
    assert session.data["candidate"]["status"] == "stale"
    assert session.data["confirmations"] == {}
    with pytest.raises(CalibrationError, match="blocking calibration evidence"):
        persist_activation(
            session,
            session_path=Path("unused-session.json"),
            active_path=Path("unused-active.json"),
        )


def test_checklist_evidence_change_after_confirmation_invalidates_candidate():
    session = CalibrationSession.start("evidence-change")
    candidate = complete_candidate(session)
    confirm_candidate(session, candidate)

    session.record_checklist_evidence(
        CALIBRATION_STAGES[0],
        observed_evidence=["evidence/repository-role-v2.txt"],
        candidate_change="repository role evidence changed",
        owner="repository-owner",
        reviewer="repository-reviewer",
        decision="PASS",
        decision_reason="Replacement evidence is complete",
    )

    assert session.data["candidate"]["status"] == "stale"
    assert session.data["confirmations"] == {}
    assert session.data["checks"]["full_self_check"]["status"] == "blocked"
    assert session.data["checks"]["governance_simulation"]["status"] == "blocked"


def test_schema_v1_migration_is_fail_closed_for_unknown_and_unbound_confirmation(tmp_path: Path):
    session = CalibrationSession.start("legacy")
    complete(session)
    session.data["schemaVersion"] = 1
    session.data["stages"][0]["checklist"]["answerType"] = "unknown"
    session.data["stages"][0]["checklist"]["answer"] = "Unknown"
    session.data["confirmations"] = {
        "reviewer": {"status": "confirmed"},
        "owner": {"status": "confirmed"},
    }
    session.data["state"] = "activated"
    session.data["active"] = {"status": "active", "configuration": {"legacy": True}}
    session.data["candidate"] = {"status": "not_prepared", "configuration": None}
    legacy = tmp_path / "legacy.json"
    legacy.write_text(json.dumps(session.data), encoding="utf-8")

    migrated = load_session(legacy)

    assert migrated.data["schemaVersion"] == 2
    assert migrated.data["stages"][0]["status"] == "blocked"
    assert migrated.data["confirmations"] == {}
    assert migrated.data["legacyConfirmationHistory"]
    assert migrated.data["state"] == "paused"
    assert migrated.data["active"]["status"] == "legacy_unverified"
    assert migrated.review()["status"] == "blocked"
    migrated.resume()
    with pytest.raises(CalibrationError, match="blocking calibration evidence"):
        migrated.prepare_candidate()


def test_session_staging_failure_cleans_first_temporary_and_restores_state(
    tmp_path: Path, monkeypatch
):
    session_path = tmp_path / "session.json"
    active_path = tmp_path / "active.json"
    original_session = b'{"originalSession":true}\n'
    original_active = b'{"originalActive":true}\n'
    session_path.write_bytes(original_session)
    active_path.write_bytes(original_active)
    session = CalibrationSession.start("staging-failure")
    candidate = complete_candidate(session)
    confirm_candidate(session, candidate)
    real_write_temporary = ai_calibrate._write_temporary

    def fail_session_staging(path: Path, content: bytes, prefix: str) -> Path:
        if path == session_path:
            raise OSError("simulated Session staging failure")
        return real_write_temporary(path, content, prefix)

    monkeypatch.setattr(ai_calibrate, "_write_temporary", fail_session_staging)
    with pytest.raises(CalibrationError, match="activation transaction failed"):
        persist_activation(session, session_path=session_path, active_path=active_path)

    assert active_path.read_bytes() == original_active
    assert session_path.read_bytes() == original_session
    assert list(tmp_path.glob("calibration-active-*")) == []
    assert session.data["state"] != "activated"


def test_session_replace_failure_restores_active_and_session_bytes(tmp_path: Path):
    session_path = tmp_path / "session.json"
    active_path = tmp_path / "active.json"
    original_session = b'{"originalSession":true}\n'
    original_active = b'{"originalActive":true}\n'
    session_path.write_bytes(original_session)
    active_path.write_bytes(original_active)
    session = CalibrationSession.start("transaction")
    candidate = complete_candidate(session)
    confirm_candidate(session, candidate)
    real_replace = ai_calibrate.os.replace
    failed = False

    def fail_session_replace(source: str | Path, destination: str | Path) -> None:
        nonlocal failed
        if Path(destination) == session_path and not failed:
            failed = True
            raise OSError("simulated Session replace failure")
        real_replace(source, destination)

    with pytest.raises(CalibrationError, match="activation transaction failed"):
        persist_activation(
            session,
            session_path=session_path,
            active_path=active_path,
            replace_fn=fail_session_replace,
        )

    assert active_path.read_bytes() == original_active
    assert session_path.read_bytes() == original_session
    assert session.data["state"] != "activated"


def test_active_replace_failure_preserves_both_original_files(tmp_path: Path):
    session_path = tmp_path / "session.json"
    active_path = tmp_path / "active.json"
    original_session = b'{"originalSession":true}\n'
    original_active = b'{"originalActive":true}\n'
    session_path.write_bytes(original_session)
    active_path.write_bytes(original_active)
    session = CalibrationSession.start("active-failure")
    candidate = complete_candidate(session)
    confirm_candidate(session, candidate)
    real_replace = ai_calibrate.os.replace
    failed = False

    def fail_active_once(source: str | Path, destination: str | Path) -> None:
        nonlocal failed
        if Path(destination) == active_path and not failed:
            failed = True
            raise OSError("simulated Active replace failure")
        real_replace(source, destination)

    with pytest.raises(CalibrationError, match="Active and Session restored"):
        persist_activation(
            session,
            session_path=session_path,
            active_path=active_path,
            replace_fn=fail_active_once,
        )

    assert active_path.read_bytes() == original_active
    assert session_path.read_bytes() == original_session


def test_session_failure_removes_transaction_paths_that_were_initially_absent(tmp_path: Path):
    session_path = tmp_path / "session.json"
    active_path = tmp_path / "active.json"
    session = CalibrationSession.start("absent-rollback")
    candidate = complete_candidate(session)
    confirm_candidate(session, candidate)
    real_replace = ai_calibrate.os.replace
    failed = False

    def fail_session_once(source: str | Path, destination: str | Path) -> None:
        nonlocal failed
        if Path(destination) == session_path and not failed:
            failed = True
            raise OSError("simulated Session replace failure")
        real_replace(source, destination)

    with pytest.raises(CalibrationError, match="Active and Session restored"):
        persist_activation(
            session,
            session_path=session_path,
            active_path=active_path,
            replace_fn=fail_session_once,
        )

    assert not active_path.exists()
    assert not session_path.exists()


def test_successful_activation_persists_matching_candidate_identity(tmp_path: Path):
    session_path = tmp_path / "session.json"
    active_path = tmp_path / "active.json"
    session = CalibrationSession.start("transaction-success")
    candidate = complete_candidate(session)
    confirm_candidate(session, candidate)

    persist_activation(session, session_path=session_path, active_path=active_path)

    persisted_session = load_session(session_path).data
    persisted_active = json.loads(active_path.read_text(encoding="utf-8"))
    assert persisted_session["state"] == "activated"
    assert persisted_active["candidateRevision"] == candidate["revision"]
    assert persisted_active["candidateDigest"] == candidate["digest"]
    assert persisted_session["active"]["configuration"] == persisted_active


def test_session_has_ten_japanese_stages_and_requires_na_reason():
    with pytest.raises(CalibrationError, match="session_id"):
        CalibrationSession.start("")
    session = CalibrationSession.start("test-session")
    assert session.data["language"] == "ja"
    assert [stage["id"] for stage in session.data["stages"]] == list(CALIBRATION_STAGES)
    assert set(session.data["stages"][0]["checklist"]["answerTypes"]) == {
        "yes_no",
        "alternative_input",
        "unknown",
        "not_applicable",
    }
    with pytest.raises(CalibrationError, match="requires a reason"):
        session.answer(CALIBRATION_STAGES[0], "N/A", answer_type="not_applicable")
    with pytest.raises(CalibrationError, match="already at the first"):
        session.back()
    with pytest.raises(CalibrationError, match="unsupported answer type"):
        session.answer(CALIBRATION_STAGES[0], "x", answer_type="invalid")
    with pytest.raises(CalibrationError, match="non-empty"):
        session.answer(CALIBRATION_STAGES[0], "", answer_type="alternative_input")
    with pytest.raises(CalibrationError, match="Y or N"):
        session.answer(CALIBRATION_STAGES[0], "maybe", answer_type="yes_no")


def test_pause_resume_back_review_and_stale_dependency_preserve_evidence():
    session = CalibrationSession.start("test-session")
    session.answer(CALIBRATION_STAGES[0], "Y", answer_type="yes_no")
    session.answer(CALIBRATION_STAGES[1], "Python", answer_type="alternative_input")
    session.answer(CALIBRATION_STAGES[2], "src", answer_type="alternative_input")
    session.pause()
    with pytest.raises(CalibrationError, match="resume"):
        session.answer(CALIBRATION_STAGES[2], "src", answer_type="alternative_input")
    session.resume()
    session.back()
    session.answer(CALIBRATION_STAGES[1], "TypeScript", answer_type="alternative_input")
    assert CALIBRATION_STAGES[2] in session.data["staleStages"]
    assert any(event["kind"] == "back" for event in session.data["events"])
    assert session.review()["status"] == "blocked"


def test_revalidate_returns_stale_stages_to_the_session_queue():
    session = CalibrationSession.start("revalidate")
    session.answer(CALIBRATION_STAGES[0], "Y", answer_type="yes_no")
    session.answer(CALIBRATION_STAGES[1], "Python")
    session.answer(CALIBRATION_STAGES[2], "src")
    session.back()
    session.answer(CALIBRATION_STAGES[1], "TypeScript")
    assert session.data["staleStages"]
    session.revalidate()
    assert session.data["staleStages"] == []
    assert session.data["currentStage"] == CALIBRATION_STAGES[2]


def test_checks_confirmations_and_atomic_activation(tmp_path: Path):
    active = tmp_path / "active.json"
    session_path = tmp_path / "session.json"
    active.write_text('{"old": true}\n', encoding="utf-8")
    session = CalibrationSession.start("test-session")
    candidate = complete_candidate(session)
    assert session.stage_self_check()["status"] == "passed"
    confirm_candidate(session, candidate)
    persist_activation(session, session_path=session_path, active_path=active)
    assert json.loads(active.read_text(encoding="utf-8"))["sessionId"] == "test-session"

    failed = CalibrationSession.start("failed-session")
    failed_candidate = complete_candidate(failed)
    confirm_candidate(failed, failed_candidate)

    def fail_replace(_source: str | Path, _destination: str | Path) -> None:
        raise OSError("simulated replacement failure")

    with pytest.raises(CalibrationError, match="consistency is unproved"):
        persist_activation(
            failed,
            session_path=session_path,
            active_path=active,
            replace_fn=fail_replace,
        )
    assert json.loads(active.read_text(encoding="utf-8"))["sessionId"] == "test-session"


def test_checks_fail_closed_before_completion_and_loader_rejects_bad_schema(tmp_path: Path):
    session = CalibrationSession.start("incomplete")
    assert session.stage_self_check()["status"] == "blocked"
    assert session.full_self_check()["status"] == "blocked"
    assert session.governance_simulation()["status"] == "blocked"
    with pytest.raises(CalibrationError, match="full self-check"):
        session.confirm(
            "reviewer",
            candidate_revision=1,
            candidate_digest="0" * 64,
        )
    with pytest.raises(CalibrationError, match="confirmation phase"):
        session.confirm(
            "invalid",
            candidate_revision=1,
            candidate_digest="0" * 64,
        )
    with pytest.raises(CalibrationError, match="blocking calibration evidence"):
        persist_activation(
            session,
            session_path=tmp_path / "session.json",
            active_path=tmp_path / "active.json",
        )
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"schemaVersion": 99, "language": "en"}), encoding="utf-8")
    with pytest.raises(CalibrationError, match="unsupported"):
        load_session(bad)


def test_session_persists_and_cli_runs_adopter_flow(tmp_path: Path):
    session_path = tmp_path / "session.json"
    active_path = tmp_path / "active.json"
    command = [sys.executable, "scripts/ai_calibrate.py", "session"]
    root = Path(__file__).resolve().parents[1]

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [*command, *args, "--session", str(session_path)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    assert run("start", "--session-id", "fixture-session").returncode == 0
    assert run("answer").returncode == 1
    assert run("confirm").returncode == 1
    assert run("not-an-action").returncode != 0
    for stage in CALIBRATION_STAGES:
        assert (
            run("answer", "--stage", stage, "--answer", "Y", "--answer-type", "yes_no").returncode
            == 0
        )
        assert run("record-evidence", *evidence_cli_args(stage)).returncode == 0
    assert run("review").returncode == 0
    assert run("full-self-check").returncode == 0
    assert run("simulate").returncode == 0
    assert run("prepare-candidate").returncode == 0
    candidate = load_session(session_path).data["candidate"]
    confirmation_identity = (
        "--candidate-revision",
        str(candidate["revision"]),
        "--candidate-digest",
        candidate["digest"],
    )
    assert run("confirm", "--phase", "reviewer", *confirmation_identity).returncode == 0
    assert run("confirm", "--phase", "owner", *confirmation_identity).returncode == 0
    result = run("activate", "--active", str(active_path))
    assert result.returncode == 0, result.stderr
    assert load_session(session_path).data["state"] == "activated"
    assert json.loads(active_path.read_text(encoding="utf-8"))["sessionId"] == "fixture-session"


def test_cli_dispatch_is_exercised_in_process(tmp_path: Path, monkeypatch):
    session_path = tmp_path / "session.json"
    active_path = tmp_path / "active.json"

    def call(*args: str) -> int:
        monkeypatch.setattr(
            sys, "argv", ["ai_calibrate", "session", *args, "--session", str(session_path)]
        )
        return ai_calibrate.main()

    assert call("start", "--session-id", "in-process") == 0
    assert (
        call("answer", "--stage", CALIBRATION_STAGES[0], "--answer", "Y", "--answer-type", "yes_no")
        == 0
    )
    assert call("back") == 0
    for stage in CALIBRATION_STAGES:
        assert call("answer", "--stage", stage, "--answer", "Y", "--answer-type", "yes_no") == 0
        assert call("record-evidence", *evidence_cli_args(stage)) == 0
    assert call("review") == 0
    assert call("pause") == 0
    assert call("resume") == 0
    assert call("stage-self-check") == 0
    assert call("full-self-check") == 0
    assert call("simulate") == 0
    assert call("prepare-candidate") == 0
    candidate = load_session(session_path).data["candidate"]
    confirmation_identity = (
        "--candidate-revision",
        str(candidate["revision"]),
        "--candidate-digest",
        candidate["digest"],
    )
    assert call("confirm", "--phase", "reviewer", *confirmation_identity) == 0
    assert call("confirm", "--phase", "owner", *confirmation_identity) == 0
    assert call("activate", "--active", str(active_path)) == 0
