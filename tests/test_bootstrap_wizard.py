import pytest

from bootstrap_wizard import (
    BOOTSTRAP_CREATION_MODE,
    BOOTSTRAP_LIFECYCLE,
    Phase,
    Session,
    WizardError,
    validate_bootstrap_record,
)


def configured_session() -> Session:
    session = Session("external-001")
    session = session.transition(
        "detect", upstream_revision="r1", detected={"root": "/tmp/project"}
    )
    session = session.transition("propose", proposal={"write": [".ai"]})
    session = session.transition("configure", configuration={"stack": "python"})
    return session.transition("review", review={"accepted": True})


def test_wizard_runs_the_explicit_happy_path():
    session = configured_session().transition("confirm", approved=True)
    assert session.phase is Phase.CONFIRMED
    assert session.to_dict()["sessionId"] == "external-001"


def test_back_clears_downstream_decisions():
    session = configured_session().transition("back")
    assert session.phase is Phase.REVIEW
    assert session.review is not None


def test_cancel_and_resume_do_not_write_to_a_repository():
    session = configured_session().transition("cancel")
    assert session.phase is Phase.CANCELLED
    resumed = session.transition("resume")
    assert resumed.phase is Phase.CONFIRM


def test_upstream_change_invalidates_all_downstream_state():
    session = configured_session().invalidate("r2")
    assert session.phase is Phase.PROPOSE
    assert session.upstream_revision == "r2"
    assert session.proposal is None
    assert session.configuration is None
    assert session.review is None


def test_confirmation_with_stale_revision_invalidates_before_confirmation():
    session = configured_session().transition("confirm", approved=True, upstream_revision="r2")
    assert session.phase is Phase.PROPOSE
    assert session.upstream_revision == "r2"


def test_invalid_transition_is_rejected():
    with pytest.raises(WizardError):
        Session("external-002").transition("confirm", approved=True)


def test_bootstrap_schema_requires_explicit_lifecycle_and_never_claims_ready():
    record = configured_session().transition("confirm", approved=True).transition("write")
    payload = record.to_dict()
    assert payload["lifecycleType"] == BOOTSTRAP_LIFECYCLE
    assert payload["creationMode"] == BOOTSTRAP_CREATION_MODE
    assert payload["readiness"] == "not_claimed"
    assert validate_bootstrap_record(payload) == []


def test_write_requires_confirmed_session_and_explicit_confirmation():
    with pytest.raises(WizardError, match="confirmed"):
        configured_session().transition("write")

    confirmed = configured_session().transition("confirm", approved=True)
    assert confirmed.transition("write").phase is Phase.WRITE


def test_schema_rejects_governed_development_claims():
    record = configured_session().transition("confirm", approved=True).transition("write").to_dict()
    record["readiness"] = "ready"
    assert any("readiness" in issue for issue in validate_bootstrap_record(record))
