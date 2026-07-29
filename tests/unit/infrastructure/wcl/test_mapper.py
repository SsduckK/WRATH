"""Tests for mapping WCL GraphQL payloads to domain models."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from wcl_analyzer.infrastructure.wcl import WclMappingError, map_report_response

FIXTURE_PATH = (
    Path(__file__).parents[3] / "fixtures" / "wcl" / "report_with_fights.json"
)


@pytest.fixture
def report_payload() -> dict[str, object]:
    """Load a synthetic WCL response without private report data."""
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_map_report_response_creates_report_and_fights(
    report_payload: dict[str, object],
) -> None:
    report = map_report_response(report_payload)

    assert report.code == "FakeReport123"
    assert report.title == "Fixture Raid Night"
    assert len(report.fights) == 2

    first_fight = report.fights[0]
    assert first_fight.id == 1
    assert first_fight.name == "First Encounter"
    assert first_fight.start_time_ms == 1_000
    assert first_fight.end_time_ms == 61_000
    assert first_fight.duration_ms == 60_000

    second_fight = report.fights[1]
    assert second_fight.id == 2
    assert second_fight.duration_ms == 120_000


@pytest.mark.parametrize(
    "missing_field",
    ["code", "title", "fights"],
)
def test_map_report_response_rejects_missing_report_fields(
    report_payload: dict[str, object],
    missing_field: str,
) -> None:
    payload = deepcopy(report_payload)
    report_data = payload["data"]["reportData"]["report"]  # type: ignore[index]
    del report_data[missing_field]  # type: ignore[index]

    with pytest.raises(WclMappingError, match=missing_field):
        map_report_response(payload)


@pytest.mark.parametrize(
    "missing_field",
    ["id", "name", "startTime", "endTime"],
)
def test_map_report_response_rejects_missing_fight_fields(
    report_payload: dict[str, object],
    missing_field: str,
) -> None:
    payload = deepcopy(report_payload)
    fights = payload["data"]["reportData"]["report"]["fights"]  # type: ignore[index]
    del fights[0][missing_field]  # type: ignore[index]

    with pytest.raises(WclMappingError, match=missing_field):
        map_report_response(payload)


def test_map_report_response_rejects_graphql_errors() -> None:
    payload = {
        "errors": [{"message": "Report not found"}],
        "data": {"reportData": {"report": None}},
    }

    with pytest.raises(WclMappingError, match="GraphQL response contains errors"):
        map_report_response(payload)
