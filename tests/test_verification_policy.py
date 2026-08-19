import pytest
from ai_verification_policy import (
    classify_immutable_workflow_pin_change,
    escalation_reasons,
    finish_quality_route,
    finish_quality_route_for_contract,
    order_checks,
    select_policy,
    verification_cache_key,
    verification_signal,
)

_PIN_BEFORE = """jobs:\n  quality:\n    steps:\n      - uses: dtolnay/rust-toolchain@e97e2d8cc328f1b50210efc529dca0028893a2d9\n"""
_PIN_AFTER = """jobs:\n  quality:\n    steps:\n      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772\n"""


def test_immutable_sha_only_workflow_change_uses_minimal_strict_groups():
    facts = classify_immutable_workflow_pin_change(
        ".github/workflows/compatibility.yml", _PIN_BEFORE, _PIN_AFTER
    )

    assert facts["eligible"] is True
    route = finish_quality_route([".github/workflows/compatibility.yml"], immutable_pin_facts=facts)
    assert route["policy"]["level"] == "strict"
    assert route["policy"]["qualityTarget"] == "quality-strict-targeted"
    assert route["policy"]["requiredGroups"] == ["quality-fast"]


@pytest.mark.parametrize(
    ("path", "before", "after"),
    [
        (
            ".github/workflows/compatibility.yml",
            _PIN_BEFORE,
            _PIN_AFTER.replace("      - uses:", "      - name: extra\n        uses:"),
        ),
        (
            ".github/workflows/compatibility.yml",
            _PIN_BEFORE,
            _PIN_AFTER.replace("6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772", "v1"),
        ),
        (
            ".github/workflows/release.yml",
            _PIN_BEFORE,
            _PIN_AFTER,
        ),
    ],
)
def test_immutable_pin_classifier_fails_closed_for_unsafe_shapes(path, before, after):
    facts = classify_immutable_workflow_pin_change(path, before, after)

    assert facts["eligible"] is False
    route = finish_quality_route([path], immutable_pin_facts=facts)
    assert route["policy"]["qualityTarget"] == "quality-full"


@pytest.mark.parametrize(
    ("path", "before", "after"),
    [
        ("README.md", _PIN_BEFORE, _PIN_AFTER),
        (".github/workflows/nested/compatibility.yml", _PIN_BEFORE, _PIN_AFTER),
        (".github/workflows/compatibility.yml", _PIN_BEFORE + "extra\n", _PIN_AFTER),
        (
            ".github/workflows/compatibility.yml",
            _PIN_BEFORE,
            _PIN_AFTER.replace("dtolnay/rust-toolchain", "actions/checkout"),
        ),
        (".github/workflows/compatibility.yml", _PIN_BEFORE, _PIN_BEFORE),
        (
            ".github/workflows/compatibility.yml",
            _PIN_BEFORE,
            _PIN_AFTER.replace(
                "@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772",
                "@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # changed",
            ),
        ),
    ],
)
def test_immutable_pin_classifier_rejects_non_exact_evidence(path, before, after):
    facts = classify_immutable_workflow_pin_change(path, before, after)

    assert facts["eligible"] is False


def test_finish_quality_route_keeps_docs_only_task_focused_but_escalates_governance_paths():
    assert (
        finish_quality_route(["docs/guide.md"])["command"]
        == "make ai-cockpit-quality GOVERNANCE_PROFILE=light"
    )
    assert (
        finish_quality_route([".ai/guards/policy.yaml"])["command"]
        == "make ai-cockpit-quality GOVERNANCE_PROFILE=strict"
    )


def test_finish_quality_route_cannot_lower_an_explicit_strict_contract_profile():
    route = finish_quality_route(["scripts/ai_generate_task_outcome.py"], requested="strict")

    assert route["policy"]["level"] == "strict"
    assert route["command"] == "make ai-cockpit-quality GOVERNANCE_PROFILE=strict"


def test_automatic_strict_governance_routes_to_targeted_groups_but_explicit_strict_is_full():
    automatic = finish_quality_route(["scripts/ai_check_reference_impact.py"])
    explicit = finish_quality_route(["scripts/ai_check_reference_impact.py"], requested="strict")

    assert automatic["policy"]["qualityTarget"] == "quality-strict-targeted"
    assert "quality-project-consistency-group" in automatic["policy"]["requiredGroups"]
    assert explicit["policy"]["qualityTarget"] == "quality-full"


def test_strict_routing_keeps_high_risk_domains_on_full_quality():
    for path in (
        ".ai/guards/policy.yaml",
        "requirements-dev.lock",
        ".github/workflows/release.yml",
        "scripts/install_ai_cockpit.py",
    ):
        route = finish_quality_route([path])
        assert route["policy"]["qualityTarget"] == "quality-full"


def test_finish_route_reclassifies_automatic_profile_but_preserves_stricter_record():
    elevated = finish_quality_route_for_contract(
        [".ai/guards/policy.yaml"],
        {"selected": "standard", "source": "automatic"},
    )
    preserved = finish_quality_route_for_contract(
        ["docs/guide.md"],
        {"selected": "strict", "source": "automatic"},
    )
    with pytest.raises(ValueError, match="cannot lower"):
        finish_quality_route_for_contract(
            [".ai/guards/policy.yaml"],
            {
                "selected": "standard",
                "source": "human_override",
            },
        )

    assert elevated["policy"]["level"] == "strict"
    assert preserved["policy"]["level"] == "strict"


def test_verification_policy_distinguishes_failure_incomplete_and_passed():
    assert verification_signal(["a"], {"a": "failed"})["value"] == "failed"
    assert verification_signal(["a"], {})["value"] == "incomplete"
    assert verification_signal(["a"], {"a": "passed"})["value"] == "passed"


def test_policy_is_monotonic_and_release_stage_is_strict_full():
    assert select_policy("task", ["README.md"], requested="light")["scope"] == "focused"
    assert select_policy("task", [".github/workflows/test.yml"])["level"] == "strict"
    assert select_policy("release", ["README.md"])["scope"] == "full"
    assert select_policy("release", ["README.md"])["level"] == "strict"
    assert select_policy("pr", ["src/app.py"])["level"] == "standard"
    assert select_policy("task", ["README.md"], requested="standard")["level"] == "standard"
    assert select_policy("task", ["requirements-dev.lock"])["level"] == "strict"
    assert select_policy("task", ["unknown.file"])["level"] == "standard"
    with pytest.raises(ValueError, match="cannot lower"):
        select_policy("task", ["requirements-dev.lock"], requested="standard")
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


def test_impact_graph_reports_declared_proof_layers_without_execution():
    from ai_verification_policy import evaluate_current_impact_graph

    graph = evaluate_current_impact_graph(profile="strict", receipt_bindings={})

    assert graph["valid"] is True
    assert graph["orderedNodes"] == ["fast", "finish", "hosted"]


def test_escalation_reasons_cover_high_risk_and_injection_signals():
    reasons = escalation_reasons(
        ["tests/test_x.py", ".github/workflows/release.yml"],
        unknown=True,
        injection=True,
        prior_failure=True,
    )
    assert reasons == ["injection_signal", "release", "test_changed_after_failure", "unknown_input"]
