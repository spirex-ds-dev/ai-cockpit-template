import sys

import ai_japanese_capability
from ai_japanese_capability import evaluate, render_markdown


def test_japanese_assessment_proves_local_fail_closed_boundaries():
    result = evaluate()

    by_id = {case["id"]: case for case in result["cases"]}
    assert by_id["ja-injection"]["status"] == "pass"
    assert by_id["ja-hidden-html"]["status"] == "pass"
    assert by_id["ja-mixed-tool"]["status"] == "pass"
    assert by_id["ja-human-decision"]["status"] == "pass"
    assert by_id["ja-document-actionability"]["status"] == "pass"


def test_japanese_assessment_keeps_unproved_general_fluency_as_a_non_claim():
    result = evaluate()
    markdown = render_markdown(result)

    by_id = {case["id"]: case for case in result["cases"]}
    assert by_id["ja-general-fluency-boundary"]["status"] == "limitation"
    assert "non-claim" in markdown
    assert "general Japanese model fluency" in markdown


def test_japanese_assessment_cli_writes_report(tmp_path, monkeypatch, capsys):
    output = tmp_path / "japanese-capability-assessment.md"
    monkeypatch.setattr(ai_japanese_capability, "REPORT_PATH", output)
    monkeypatch.setattr(sys, "argv", ["ai_japanese_capability.py", "--write"])

    assert ai_japanese_capability.main() == 0
    assert output.is_file()
    assert "Japanese Capability Assessment" in output.read_text(encoding="utf-8")
    assert "blockingFindings" in capsys.readouterr().out
