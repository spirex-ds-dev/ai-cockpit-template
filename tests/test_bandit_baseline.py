import hashlib
import json
import sys
from pathlib import Path

import check_bandit_baseline


ROOT = Path(__file__).resolve().parents[1]


def test_load_baseline_rejects_non_objects(tmp_path):
    baseline = tmp_path / "bandit_low_risk_baseline.json"
    baseline.write_text("[]", encoding="utf-8")

    try:
        check_bandit_baseline.load_baseline(baseline)
    except ValueError as exc:
        assert "baseline must be a JSON object" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_current_digest_is_order_independent(tmp_path):
    payload = {
        "results": [
            {
                "test_id": "B201",
                "issue_severity": "LOW",
                "filename": "scripts/b.py",
                "issue_text": "second",
            },
            {
                "test_id": "B101",
                "issue_severity": "HIGH",
                "filename": "scripts/a.py",
                "issue_text": "first",
            },
        ]
    }

    evidence = tmp_path / "bandit.json"
    evidence.write_text(json.dumps(payload), encoding="utf-8")
    count, digest = check_bandit_baseline.current_digest(evidence)

    expected_items = [
        {"testId": "B101", "severity": "HIGH", "filename": "scripts/a.py", "issue": "first"},
        {"testId": "B201", "severity": "LOW", "filename": "scripts/b.py", "issue": "second"},
    ]
    expected_digest = hashlib.sha256(
        json.dumps(expected_items, sort_keys=True).encode("utf-8")
    ).hexdigest()

    assert count == 2
    assert digest == expected_digest


def test_main_accepts_matching_baseline(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    baseline = repo / ".ai" / "cockpit" / "bandit_low_risk_baseline.json"
    baseline.parent.mkdir(parents=True)
    digest = hashlib.sha256(json.dumps([], sort_keys=True).encode("utf-8")).hexdigest()
    baseline.write_text(json.dumps({"count": 0, "digest": digest}), encoding="utf-8")

    monkeypatch.setattr(check_bandit_baseline, "ROOT", repo)
    monkeypatch.setattr(check_bandit_baseline, "BASELINE", baseline)
    evidence = repo / "bandit.json"
    evidence.write_text(json.dumps({"results": []}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check_bandit_baseline.py", "--input", str(evidence)])

    assert check_bandit_baseline.main() == 0


def test_main_rejects_mismatched_baseline(tmp_path, monkeypatch, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    baseline = repo / ".ai" / "cockpit" / "bandit_low_risk_baseline.json"
    baseline.parent.mkdir(parents=True)
    baseline.write_text(json.dumps({"count": 1, "digest": "1" * 64}), encoding="utf-8")

    monkeypatch.setattr(check_bandit_baseline, "ROOT", repo)
    monkeypatch.setattr(check_bandit_baseline, "BASELINE", baseline)
    evidence = repo / "bandit.json"
    evidence.write_text(json.dumps({"results": []}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check_bandit_baseline.py", "--input", str(evidence)])

    assert check_bandit_baseline.main() == 1
    assert "bandit baseline drifted" in capsys.readouterr().err
