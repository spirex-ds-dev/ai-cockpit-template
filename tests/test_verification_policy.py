import pytest
from ai_verification_policy import (
    escalation_reasons,
    order_checks,
    select_policy,
    verification_cache_key,
    verification_signal,
)


def test_verification_policy_distinguishes_failure_incomplete_and_passed():
    assert verification_signal(["a"], {"a": "failed"})["value"] == "failed"
    assert verification_signal(["a"], {})["value"] == "incomplete"
    assert verification_signal(["a"], {"a": "passed"})["value"] == "passed"


def test_policy_is_monotonic_and_release_is_full():
    assert select_policy("task", ["README.md"], requested="light")["scope"] == "focused"
    assert (
        select_policy("task", [".github/workflows/test.yml"], requested="light")["level"]
        == "strict"
    )
    assert select_policy("release", ["README.md"])["scope"] == "full"
    assert select_policy("pr", ["src/app.py"])["level"] == "standard"
    assert select_policy("task", ["README.md"], requested="standard")["level"] == "standard"
    with pytest.raises(ValueError, match="unsupported policy level"):
        select_policy("task", [], requested="unknown")


def test_cache_key_requires_and_binds_all_inputs():
    inputs = {
        name: name
        for name in ("base", "diff", "command", "tool", "dependency", "environment", "config")
    }
    first = verification_cache_key(inputs)
    changed = dict(inputs, config="changed")
    assert first != verification_cache_key(changed)
    with pytest.raises(ValueError, match="cache key inputs missing"):
        verification_cache_key({"base": "x"})


def test_check_dag_is_deterministic_and_fail_closed():
    assert order_checks({"tests": ["scope"], "scope": [], "trust": ["scope"]}) == [
        "scope",
        "tests",
        "trust",
    ]
    with pytest.raises(ValueError, match="unknown check dependencies"):
        order_checks({"tests": ["missing"]})
    with pytest.raises(ValueError, match="cycle"):
        order_checks({"a": ["b"], "b": ["a"]})


def test_escalation_reasons_cover_high_risk_and_injection_signals():
    reasons = escalation_reasons(
        ["tests/test_x.py", ".github/workflows/release.yml"],
        unknown=True,
        injection=True,
        prior_failure=True,
    )
    assert reasons == ["injection_signal", "release", "test_changed_after_failure", "unknown_input"]
