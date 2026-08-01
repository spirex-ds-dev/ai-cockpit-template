from scripts import ai_performance_budget


def test_baseline_collects_until_a_profile_has_enough_samples():
    report = ai_performance_budget.build_baseline(
        [{"performanceReport": {"profile": "light", "totalDurationMs": 100}}],
        minimum_samples=3,
    )

    assert report["profiles"]["light"] == {
        "sampleCount": 1,
        "status": "collecting",
        "p95Ms": None,
    }


def test_baseline_calculates_profile_p95_from_receipts_only():
    report = ai_performance_budget.build_baseline(
        [
            {"performanceReport": {"profile": "strict", "totalDurationMs": duration}}
            for duration in (100, 200, 300)
        ],
        minimum_samples=3,
    )

    assert report["measurementSource"] == "local_quality_summaries"
    assert report["profiles"]["strict"] == {
        "sampleCount": 3,
        "status": "baseline_ready",
        "p95Ms": 300,
    }
