import json

from ai_start import configuration_gate_issue


def write_runtime(tmp_path, *, readiness="not_ready", quality="not_configured"):
    path = tmp_path / ".ai" / "cockpit" / "adoption-runtime-verification.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"readiness": readiness, "projectQualityState": quality}), encoding="utf-8"
    )


def test_template_or_non_adopter_can_start_without_configuration_evidence(tmp_path):
    assert configuration_gate_issue("feature", root=tmp_path) is None


def test_adopter_not_ready_is_blocked_for_ordinary_work(tmp_path):
    write_runtime(tmp_path)
    issue = configuration_gate_issue("feature", root=tmp_path)
    assert issue is not None
    assert "Configuration Required" in issue


def test_configuration_work_item_is_the_explicit_exception(tmp_path):
    write_runtime(tmp_path)
    assert configuration_gate_issue("configure_ai_cockpit", root=tmp_path) is None


def test_explicit_ready_runtime_evidence_allows_ordinary_work(tmp_path):
    write_runtime(tmp_path, readiness="ready", quality="configured")
    assert configuration_gate_issue("feature", root=tmp_path) is None


def test_malformed_runtime_evidence_fails_closed(tmp_path):
    path = tmp_path / ".ai" / "cockpit" / "adoption-runtime-verification.json"
    path.parent.mkdir(parents=True)
    path.write_text("not-json", encoding="utf-8")
    assert "unreadable" in configuration_gate_issue("feature", root=tmp_path)
