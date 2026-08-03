from __future__ import annotations

from ai_observability import AiObservability, AiObservabilitySink, LifecycleTimingLedger


class _Sink(AiObservabilitySink):
    def __init__(self) -> None:
        self.events = []

    def record(self, event) -> None:
        self.events.append(event)


def test_phase_ledger_reports_local_compute_and_unknown_external_waits() -> None:
    ledger = LifecycleTimingLedger(work_item_id="timing-item")

    ledger.start("preflight", at_ms=100)
    ledger.finish("preflight", at_ms=145, cache_outcome="miss")

    report = ledger.report()

    assert report["localComputeMs"] == 45
    assert report["providerWaitMs"] == "unknown"
    assert report["humanWaitMs"] == "unknown"
    assert report["phases"] == [
        {"phase": "preflight", "durationMs": 45, "executionCount": 1, "cacheOutcome": "miss"}
    ]


def test_phase_ledger_rejects_unpaired_and_negative_phase_times() -> None:
    ledger = LifecycleTimingLedger(work_item_id="timing-item")

    assert ledger.finish("finish", at_ms=20) is False
    ledger.start("finish", at_ms=30)
    assert ledger.finish("finish", at_ms=20) is False
    assert ledger.report()["phases"] == []


def test_phase_ledger_counts_repeated_execution_and_no_evidence_claim() -> None:
    ledger = LifecycleTimingLedger(work_item_id="timing-item")

    assert ledger.report()["localComputeMs"] == "unknown"
    ledger.start("verification", at_ms=10)
    ledger.finish("verification", at_ms=20, cache_outcome="miss")
    ledger.start("verification", at_ms=30)
    ledger.finish("verification", at_ms=35, cache_outcome="hit")

    assert ledger.report()["phases"] == [
        {"phase": "verification", "durationMs": 15, "executionCount": 2, "cacheOutcome": "mixed"}
    ]


def test_observability_emits_a_source_bound_phase_measurement() -> None:
    sink = _Sink()
    observability = AiObservability(sinks=[sink])

    observability.lifecycle_phase_finished("preflight", duration_ms=12, cache_outcome="miss")

    assert sink.events[0].to_dict()["eventType"] == "lifecycle_phase_finished"
    assert sink.events[0].to_dict()["fields"] == {
        "phase": "preflight",
        "durationMs": 12,
        "cacheOutcome": "miss",
    }
