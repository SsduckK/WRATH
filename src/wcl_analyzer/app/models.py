"""Application result models shared with presentation layers."""

from dataclasses import dataclass
from datetime import datetime

from wcl_analyzer.domain import Report


@dataclass(frozen=True, slots=True)
class ApiRateLimitStatus:
    """Latest API point usage returned by a remote data source."""

    limit_per_hour: int
    points_spent: float
    points_remaining: float
    reset_in_seconds: int


@dataclass(frozen=True, slots=True)
class TokenStatus:
    """Safe token lifetime information that never exposes token contents."""

    available: bool
    expires_at: datetime | None
    remaining_seconds: int | None


@dataclass(frozen=True, slots=True)
class ReportLoadResult:
    """A loaded report and optional remote API usage metadata."""

    report: Report
    rate_limit: ApiRateLimitStatus | None = None
