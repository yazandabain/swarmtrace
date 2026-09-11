import pytest

from swarmtrace.load import classify_revision, parse_utc_timestamp


def test_verified_moderator_revision() -> None:
    record = {"label": "[Admin1]", "ip16": "2.202"}

    assert classify_revision(record) == "moderator"


def test_admin1_with_wrong_ip_is_not_verified_moderator() -> None:
    record = {"label": "[Admin1]", "ip16": "20.114"}

    assert classify_revision(record) == "suspicious"


def test_admin2_is_ambiguous() -> None:
    record = {"label": "[Admin2]", "ip16": "20.168"}

    assert classify_revision(record) == "ambiguous"


def test_person22_is_ambiguous() -> None:
    record = {"label": "[Person22]", "ip16": "20.165"}

    assert classify_revision(record) == "ambiguous"


def test_missing_label() -> None:
    record = {"label": None, "ip16": "20.168"}

    assert classify_revision(record) == "missing"


def test_blank_label() -> None:
    record = {"label": "   ", "ip16": "20.168"}

    assert classify_revision(record) == "missing"


def test_normal_label_is_suspicious() -> None:
    record = {"label": "AgentResearcherQZX", "ip16": "20.168"}

    assert classify_revision(record) == "suspicious"


def test_parse_utc_timestamp() -> None:
    timestamp = parse_utc_timestamp("2026-06-18T18:22:50Z")

    assert timestamp.isoformat() == "2026-06-18T18:22:50+00:00"


def test_non_utc_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse_utc_timestamp("2026-06-18T20:22:50+02:00")


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse_utc_timestamp("2026-06-18T18:22:50")
