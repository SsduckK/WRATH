"""Unit tests for report and fight domain models."""

import pytest

from wcl_analyzer.domain import Fight, Report


def test_fight_exposes_report_relative_duration() -> None:
    fight = Fight(
        id=1,
        name="Test Encounter",
        start_time_ms=1_000,
        end_time_ms=4_500,
    )
    print(f"duration_ms: {fight.duration_ms}")

    assert fight.duration_ms == 3_500


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("id", 0),
        ("name", "  "),
        ("start_time_ms", -1),
    ],
)
def test_fight_rejects_invalid_required_values(
    field_name: str,
    invalid_value: int | str,
) -> None:
    values: dict[str, int | str] = {
        "id": 1,
        "name": "Test Encounter",
        "start_time_ms": 1_000,
        "end_time_ms": 4_500,
    }
    values[field_name] = invalid_value

    with pytest.raises(ValueError):
        Fight(**values)  # type: ignore[arg-type]


def test_fight_rejects_reversed_time_range() -> None:
    with pytest.raises(ValueError, match="end_time_ms"):
        Fight(
            id=1,
            name="Test Encounter",
            start_time_ms=4_500,
            end_time_ms=1_000,
        )


def test_report_contains_immutable_fight_collection() -> None:
    fight = Fight(
        id=1,
        name="Test Encounter",
        start_time_ms=1_000,
        end_time_ms=4_500,
    )

    report = Report(code="ABC123", title="Test Report", fights=(fight,))

    assert report.fights == (fight,)
    assert report.get_fight(1) is fight
    assert report.get_fight(999) is None


@pytest.mark.parametrize(
    ("code", "title"),
    [
        ("", "Test Report"),
        ("ABC123", "  "),
    ],
)
def test_report_rejects_empty_required_values(code: str, title: str) -> None:
    with pytest.raises(ValueError):
        Report(code=code, title=title)


def test_report_rejects_duplicate_report_local_fight_ids() -> None:
    first_fight = Fight(
        id=1,
        name="First Encounter",
        start_time_ms=0,
        end_time_ms=1_000,
    )
    duplicate_id_fight = Fight(
        id=1,
        name="Second Encounter",
        start_time_ms=2_000,
        end_time_ms=3_000,
    )

    with pytest.raises(ValueError, match="unique"):
        Report(
            code="ABC123",
            title="Test Report",
            fights=(first_fight, duplicate_id_fight),
        )
