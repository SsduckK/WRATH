"""Interfaces required by application services."""

from typing import Protocol

from wcl_analyzer.app.models import ReportLoadResult, TokenStatus


class ReportRepository(Protocol):
    """Load report metadata from a configured data source."""

    def get_report(self, report_code: str) -> ReportLoadResult:
        """Return a report result identified by its normalized code."""
        ...


class ReportLoader(Protocol):
    """Application use case exposed to presentation layers."""

    def load_report(self, report_input: str) -> ReportLoadResult:
        """Load a report result from a code or supported URL."""
        ...


class TokenStatusProvider(Protocol):
    """Expose token lifetime metadata without exposing credentials."""

    def get_status(self) -> TokenStatus:
        """Return the current safe token status."""
        ...
