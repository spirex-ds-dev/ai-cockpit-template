from pathlib import Path

from check_real_absurd_injection_docs import CASE_IDS, check_repository


ROOT = Path(__file__).resolve().parents[1]


def test_real_absurd_injection_documents_are_complete_and_aligned() -> None:
    assert check_repository(ROOT) == []


def test_real_absurd_injection_documents_define_all_twelve_case_ids() -> None:
    assert CASE_IDS == tuple(f"RAI-{number:02d}" for number in range(1, 13))
