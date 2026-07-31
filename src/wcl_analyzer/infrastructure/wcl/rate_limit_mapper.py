"""Map WCL rate-limit data to an application status model."""

from collections.abc import Mapping

from wcl_analyzer.app import ApiRateLimitStatus
from wcl_analyzer.infrastructure.wcl.mapper import WclMappingError


def map_rate_limit_response(
    payload: Mapping[str, object],
) -> ApiRateLimitStatus:
    """Map ``data.rateLimitData`` from a WCL GraphQL response."""
    data = _required_mapping(payload, "data", "response")
    rate_limit = _required_mapping(data, "rateLimitData", "data")

    limit_per_hour = _required_int(rate_limit, "limitPerHour", "rateLimitData")
    points_spent = _required_number(
        rate_limit,
        "pointsSpentThisHour",
        "rateLimitData",
    )
    reset_in_seconds = _required_int(
        rate_limit,
        "pointsResetIn",
        "rateLimitData",
    )

    if limit_per_hour <= 0:
        raise WclMappingError("rateLimitData.limitPerHour must be positive")
    if points_spent < 0:
        raise WclMappingError("rateLimitData.pointsSpentThisHour must not be negative")
    if reset_in_seconds < 0:
        raise WclMappingError("rateLimitData.pointsResetIn must not be negative")

    return ApiRateLimitStatus(
        limit_per_hour=limit_per_hour,
        points_spent=points_spent,
        points_remaining=max(0.0, limit_per_hour - points_spent),
        reset_in_seconds=reset_in_seconds,
    )


def _required_mapping(
    container: Mapping[str, object],
    field: str,
    location: str,
) -> Mapping[str, object]:
    value = _required_value(container, field, location)
    if not isinstance(value, Mapping):
        raise WclMappingError(f"{location}.{field} must be an object")
    return value


def _required_int(
    container: Mapping[str, object],
    field: str,
    location: str,
) -> int:
    value = _required_value(container, field, location)
    if isinstance(value, bool) or not isinstance(value, int):
        raise WclMappingError(f"{location}.{field} must be an integer")
    return value


def _required_number(
    container: Mapping[str, object],
    field: str,
    location: str,
) -> float:
    value = _required_value(container, field, location)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise WclMappingError(f"{location}.{field} must be a number")
    return float(value)


def _required_value(
    container: Mapping[str, object],
    field: str,
    location: str,
) -> object:
    if field not in container or container[field] is None:
        raise WclMappingError(f"required field is missing: {location}.{field}")
    return container[field]
