"""Interfaces required by application services."""

from typing import Protocol

from wcl_analyzer.domain import Report


class ReportRepository(Protocol):
    """Load report metadata from a configured data source."""

    def get_report(self, report_code: str) -> Report:
        """Return a report identified by its normalized code."""
        ...
