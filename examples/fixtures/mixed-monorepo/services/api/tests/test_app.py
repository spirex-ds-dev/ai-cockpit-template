from services.api.app import health


def test_health() -> None:
    assert health() == "ok"
