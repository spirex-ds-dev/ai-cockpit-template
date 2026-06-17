import subprocess


def test_check_ai_pr_uses_aggregate_validator():
    result = subprocess.run(
        ["make", "-n", "check-ai-pr", "AI_BASE_COMMIT=abc123"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert 'scripts/ai_check_pr.py --base "abc123"' in result.stdout
