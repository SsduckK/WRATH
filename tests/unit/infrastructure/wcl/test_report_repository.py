"""Tests for loading reports through the WCL repository."""

import json
from collections.abc import Mapping
from pathlib import Path

import pytest

from wcl_analyzer.app import ReportService
from wcl_analyzer.infrastructure.wcl import WclReportRepository, WclRepositoryError
from wcl_analyzer.infrastructure.wcl.queries import (
    FIGHT_PLAYER_STATS_QUERY,
    REPORT_WITH_FIGHTS_QUERY,
)

FIXTURE_PATH = (
    Path(__file__).parents[3] / "fixtures" / "wcl" / "report_with_fights.json"
)


class FakeGraphqlClient:
    """Return a fixed payload while recording the GraphQL request."""

    def __init__(self, payload: Mapping[str, object]) -> None:
        self.payload = payload
        self.queries: list[str] = []
        self.variables: list[Mapping[str, object]] = []

    def execute(
        self,
        *,
        query: str,
        variables: Mapping[str, object],
    ) -> Mapping[str, object]:
        self.queries.append(query)
        self.variables.append(variables)
        return self.payload


def load_fixture() -> dict[str, object]:
    """Load the synthetic WCL report response."""
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_get_report_executes_query_with_separate_variables() -> None:
    client = FakeGraphqlClient(load_fixture())
    repository = WclReportRepository(client)

    result = repository.get_report("FakeReport123")

    assert client.queries == [REPORT_WITH_FIGHTS_QUERY]
    assert client.variables == [{"code": "FakeReport123"}]
    assert result.report.code == "FakeReport123"
    assert [fight.id for fight in result.report.fights] == [1, 2]
    assert result.rate_limit is not None
    assert result.rate_limit.points_remaining == 3_482.5


def test_report_service_loads_fixture_through_wcl_repository() -> None:
    client = FakeGraphqlClient(load_fixture())
    repository = WclReportRepository(client)
    service = ReportService(repository)

    result = service.load_report(
        "https://www.warcraftlogs.com/reports/FakeReport123#fight=2"
    )

    assert result.report.title == "Fixture Raid Night"
    assert result.report.get_fight(2) is not None
    assert client.variables == [{"code": "FakeReport123"}]


def test_get_report_rejects_mismatched_response_code() -> None:
    payload = load_fixture()
    payload["data"]["reportData"]["report"]["code"] = "OtherReport"  # type: ignore[index]
    repository = WclReportRepository(FakeGraphqlClient(payload))

    with pytest.raises(WclRepositoryError, match="does not match"):
        repository.get_report("FakeReport123")


def test_get_fight_player_stats_requests_only_selected_fight() -> None:
    report = (
        ReportService(WclReportRepository(FakeGraphqlClient(load_fixture())))
        .load_report("FakeReport123")
        .report
    )
    fight = report.fights[0]
    payload = {
        "data": {
            "reportData": {
                "report": {
                    "damage": {"data": {"entries": [{"id": 101, "total": 60_000}]}}
                }
            }
        }
    }
    client = FakeGraphqlClient(payload)
    repository = WclReportRepository(client)

    result = repository.get_fight_player_stats(report, fight)

    assert client.queries == [FIGHT_PLAYER_STATS_QUERY]
    assert client.variables == [{"code": "FakeReport123", "fightIDs": [1]}]
    assert result.get_player(101) is not None
    assert result.get_player(101).dps == 1_000  # type: ignore[union-attr]
