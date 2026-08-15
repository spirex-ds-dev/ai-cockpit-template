import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
RESULTS_PATH = ROOT / "docs/reference/comprehension-validation-results.json"


def test_pending_results_fail_closed_without_reader_evidence():
    assert RESULTS_PATH.exists(), "the study must publish an explicit pending result"

    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))

    assert results["status"] == "comprehension_unverified"
    assert results["documentRevision"] == "a478f1a81608c5b70baed6818c68c0ac8890a336"
    assert results["requiredLanguages"] == ["en", "zh-CN", "ja"]
    assert results["responses"] == []
    assert results["claimAuthorized"] is False
    assert results["missingEvidence"] == [
        "independent nontechnical reader response for en",
        "independent nontechnical reader response for zh-CN",
        "independent nontechnical reader response for ja",
    ]


def test_pending_results_publish_the_sample_boundary():
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))

    assert results["minimumSample"] == {"en": 1, "zh-CN": 1, "ja": 1}
    assert results["limitations"] == [
        "No independent reader responses have been ingested.",
        "Agent or author answers are not participant evidence.",
        "A three-reader bounded sample cannot establish general-population comprehension.",
    ]
