"""Tests for WCL rate-limit response mapping."""

import pytest

from wcl_analyzer.infrastructure.wcl import (
    WclMappingError,
    map_rate_limit_response,
)


def test_map_rate_limit_response_calculates_remaining_points() -> None:
    payload = {
        "data": {
            "rateLimitData": {
                "limitPerHour": 3_600,
                "pointsSpentThisHour": 117.5,
                "pointsResetIn": 1_800,
                "unknownField": "ignored",
            }
        }
    }

    status = map_rate_limit_response(payload)

    assert status.limit_per_hour == 3_600
    assert status.points_spent == 117.5
    assert status.points_remaining == 3_482.5
    assert status.reset_in_seconds == 1_800


@pytest.mark.parametrize(
    "missing_field",
    ["limitPerHour", "pointsSpentThisHour", "pointsResetIn"],
)
def test_map_rate_limit_response_rejects_missing_fields(
    missing_field: str,
) -> None:
    rate_limit: dict[str, object] = {
        "limitPerHour": 3_600,
        "pointsSpentThisHour": 117.5,
        "pointsResetIn": 1_800,
    }
    del rate_limit[missing_field]

    with pytest.raises(WclMappingError, match=missing_field):
        map_rate_limit_response({"data": {"rateLimitData": rate_limit}})
