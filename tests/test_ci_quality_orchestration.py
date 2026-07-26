from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPATIBILITY = ROOT / ".github" / "workflows" / "compatibility.yml"
SMOKE = ROOT / ".github" / "workflows" / "smoke.yml"
MAKEFILE = ROOT / "Makefile"


def test_python_matrix_uses_lightweight_compatibility_command():
    workflow = COMPATIBILITY.read_text(encoding="utf-8")

    assert "os: [ubuntu-latest, macos-latest]" in workflow
    assert 'python: ["3.10", "3.11", "3.14"]' in workflow
    assert "Run Python compatibility tests" in workflow
    assert "run: make compatibility-test" in workflow
    assert "run: make quality" not in workflow
    assert "timeout-minutes: 10" in workflow


def test_full_quality_has_one_workflow_owner():
    compatibility = COMPATIBILITY.read_text(encoding="utf-8")
    smoke = SMOKE.read_text(encoding="utf-8")

    assert compatibility.count("make quality") == 0
    assert smoke.count("make quality") == 1
    assert "Run repository quality gates" in smoke


def test_compatibility_target_disables_coverage_overhead():
    makefile = MAKEFILE.read_text(encoding="utf-8")
    target = makefile.split("compatibility-test:", 1)[1].split("\n\n", 1)[0]

    assert "pytest -q --no-cov" in target
    assert "tests/test_input_trust.py" in target
    assert "tests/test_input_trust_corpus.py" in target
    assert "tests/test_workflows.py" in target
    assert "tests/test_ci_quality_orchestration.py" in target
