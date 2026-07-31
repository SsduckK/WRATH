"""Interfaces required by application services."""

from typing import Protocol

from wcl_analyzer.app.models import ReportLoadResult, TokenStatus
from wcl_analyzer.domain import Fight, FightPlayerStats, Report


class ReportRepository(Protocol):
    """Load report metadata from a configured data source."""

    def get_report(self, report_code: str) -> ReportLoadResult:
        """Return a report result identified by its normalized code."""
        ...

    def get_fight_player_stats(
        self,
        report: Report,
        fight: Fight,
    ) -> FightPlayerStats:
        """Return aggregate player values for one fight."""
        ...


class ReportLoader(Protocol):
    """Application use case exposed to presentation layers."""

    def load_report(self, report_input: str) -> ReportLoadResult:
        """Load a report result from a code or supported URL."""
        ...

    def load_fight_player_stats(
        self,
        report: Report,
        fight: Fight,
    ) -> FightPlayerStats:
        """Load aggregate player values for one selected fight."""
        ...


class TokenStatusProvider(Protocol):
    """Expose token lifetime metadata without exposing credentials."""

    def get_status(self) -> TokenStatus:
        """Return the current safe token status."""
        ...
