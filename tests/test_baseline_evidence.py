import ai_baseline_evidence


def test_capture_records_commit_and_unavailable_measurements(tmp_path):
    import subprocess

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("x")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=tmp_path, check=True)
    evidence = ai_baseline_evidence.capture_baseline(tmp_path, "HEAD")
    assert len(evidence["commit"]) == 40
    assert evidence["coverage"]["status"] == "unavailable"
    assert evidence["fileCount"] == 1


def test_compare_surfaces_regression_and_missing_baseline():
    baseline = {
        "commit": "a",
        "fileCount": 3,
        "protectedAssets": ["security.yml"],
        "coverage": {"status": "unavailable"},
        "test": {"status": "passed"},
        "scenario": {"status": "passed"},
    }
    current = {"commit": "b", "fileCount": 2, "protectedAssets": []}
    result = ai_baseline_evidence.compare_baseline(baseline, current)
    assert result["status"] == "regressed"
    assert any("protected assets" in item for item in result["findings"])


def test_digest_is_stable():
    evidence = {"commit": "a", "fileCount": 1}
    assert ai_baseline_evidence.evidence_digest(evidence) == ai_baseline_evidence.evidence_digest(
        evidence
    )
