import ai_check_budget_impact


def test_budget_overrun_requires_repayment_work_item():
    issues = ai_check_budget_impact.validate_budget_impact(
        {"budgetImpact": {"approved": False}},
        {"pythonLines": 101},
        {"max": {"pythonLines": 100}},
    )
    assert "pythonLines exceeds policy max" in issues[0]
    assert "repaymentWorkItem" in issues[1]


def test_budget_with_explicit_repayment_is_allowed():
    assert (
        ai_check_budget_impact.validate_budget_impact(
            {
                "budgetImpact": {
                    "approved": True,
                    "repaymentWorkItem": "budget-repair",
                    "repaymentRecords": ["record-1"],
                }
            },
            {"pythonLines": 101},
            {"max": {"pythonLines": 100}},
        )
        == []
    )
