"""Interfaces required by application services."""

from typing import Protocol

from wcl_analyzer.domain import Report


class ReportRepository(Protocol):
    """Load report metadata from a configured data source."""

    def get_report(self, report_code: str) -> Report:
        """Return a report identified by its normalized code."""
        ...


class ReportLoader(Protocol):
    """Application use case exposed to presentation layers."""

    def load_report(self, report_input: str) -> Report:
        """Load a report from a code or supported URL."""
        ...
