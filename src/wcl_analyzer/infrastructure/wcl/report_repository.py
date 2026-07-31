"""WCL implementation of the application report repository."""

from collections.abc import Mapping
from typing import Protocol

from wcl_analyzer.app import ReportLoadResult
from wcl_analyzer.domain import Fight, FightPlayerStats, Report
from wcl_analyzer.infrastructure.wcl.fight_stats_mapper import (
    map_fight_player_stats,
)
from wcl_analyzer.infrastructure.wcl.mapper import map_report_response
from wcl_analyzer.infrastructure.wcl.queries import (
    FIGHT_PLAYER_STATS_QUERY,
    REPORT_WITH_FIGHTS_QUERY,
)
from wcl_analyzer.infrastructure.wcl.rate_limit_mapper import (
    map_rate_limit_response,
)


class GraphqlClient(Protocol):
    """Minimal GraphQL client capability required by this repository."""

    def execute(
        self,
        *,
        query: str,
        variables: Mapping[str, object],
    ) -> Mapping[str, object]:
        """Execute a GraphQL document and return its decoded response."""
        ...


class WclRepositoryError(ValueError):
    """Raised when WCL returns data inconsistent with the request."""


class WclReportRepository:
    """Load WCL report metadata and map it to domain models."""

    def __init__(self, client: GraphqlClient) -> None:
        self._client = client

    def get_report(self, report_code: str) -> ReportLoadResult:
        """Request one report and its fight list from WCL."""
        payload = self._client.execute(
            query=REPORT_WITH_FIGHTS_QUERY,
            variables={"code": report_code},
        )
        report = map_report_response(payload)

        if report.code != report_code:
            raise WclRepositoryError(
                "WCL response report code does not match the requested code"
            )

        return ReportLoadResult(
            report=report,
            rate_limit=map_rate_limit_response(payload),
        )

    def get_fight_player_stats(
        self,
        report: Report,
        fight: Fight,
    ) -> FightPlayerStats:
        """Request aggregate tables for one selected fight only."""
        payload = self._client.execute(
            query=FIGHT_PLAYER_STATS_QUERY,
            variables={"code": report.code, "fightIDs": [fight.id]},
        )
        return map_fight_player_stats(
            payload,
            report.code,
            fight,
            report.get_fight_participants(fight),
        )
