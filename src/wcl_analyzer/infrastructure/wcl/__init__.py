"""Warcraft Logs v2 API infrastructure."""

from wcl_analyzer.infrastructure.wcl.auth import (
    WclAuthenticationError,
    WclTokenProvider,
)
from wcl_analyzer.infrastructure.wcl.client import (
    WclClientError,
    WclGraphqlClient,
    WclGraphqlError,
    WclNetworkError,
    WclRateLimitError,
)
from wcl_analyzer.infrastructure.wcl.mapper import (
    WclMappingError,
    map_report_response,
)
from wcl_analyzer.infrastructure.wcl.report_repository import (
    GraphqlClient,
    WclReportRepository,
    WclRepositoryError,
)

__all__ = [
    "GraphqlClient",
    "WclAuthenticationError",
    "WclClientError",
    "WclGraphqlClient",
    "WclGraphqlError",
    "WclMappingError",
    "WclNetworkError",
    "WclRateLimitError",
    "WclReportRepository",
    "WclRepositoryError",
    "WclTokenProvider",
    "map_report_response",
]
