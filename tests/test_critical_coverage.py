from check_critical_coverage import CRITICAL_MINIMUMS, coverage_failures


def report_with(percent: float) -> dict:
    return {
        "files": {
            path: {"summary": {"percent_covered": percent}}
            for path in CRITICAL_MINIMUMS
        }
    }


def test_critical_coverage_accepts_values_at_or_above_floors():
    report = {
        "files": {
            path: {"summary": {"percent_covered": minimum}}
            for path, minimum in CRITICAL_MINIMUMS.items()
        }
    }

    assert coverage_failures(report) == []


def test_critical_coverage_reports_missing_and_regressed_files():
    report = report_with(100.0)
    missing = next(iter(CRITICAL_MINIMUMS))
    regressed = list(CRITICAL_MINIMUMS)[1]
    del report["files"][missing]
    report["files"][regressed]["summary"]["percent_covered"] = 0.0

    failures = coverage_failures(report)
    assert any(failure.startswith(f"{missing}: missing") for failure in failures)
    assert any(failure.startswith(f"{regressed}: 0.00%") for failure in failures)
