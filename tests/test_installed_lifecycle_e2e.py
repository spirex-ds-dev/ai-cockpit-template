from scripts.installed_lifecycle_e2e import classify_run


def test_python_fixture_is_real_and_tracks_lifecycle():
    phases = ["install", "configure", "update", "rollback", "disable", "enable", "uninstall"]
    result = classify_run("python", phases, True)
    assert result["evidenceKind"] == "local_real_execution" and result["phases"] == phases


def test_unavailable_toolchain_is_not_run():
    result = classify_run("java", ["install", "build"], False)
    assert result["evidenceKind"] == "not_run" and result["phases"] == []


def test_simulation_is_distinguished():
    assert (
        classify_run("typescript", ["install"], True, simulated=True)["evidenceKind"]
        == "simulation"
    )


def test_phase_evidence_is_traceable():
    result = classify_run("python", ["install", "rollback"], True)
    assert result["stack"] == "python" and "rollback" in result["phases"]
