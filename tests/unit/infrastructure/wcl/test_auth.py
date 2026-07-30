"""Tests for WCL client-credentials token handling."""

from collections.abc import Mapping
from datetime import UTC, datetime

import pytest

from wcl_analyzer.infrastructure.wcl.auth import (
    WclAuthenticationError,
    WclTokenProvider,
)


class FakeResponse:
    """Small response double for token endpoint tests."""

    def __init__(self, status_code: int, payload: Mapping[str, object]) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Mapping[str, object]:
        return self._payload


class FakeSession:
    """Record token requests and return queued responses."""

    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses = responses
        self.requests: list[dict[str, object]] = []

    def post(self, url: str, **kwargs: object) -> FakeResponse:
        self.requests.append({"url": url, **kwargs})
        return self._responses.pop(0)


def test_get_access_token_requests_and_caches_token() -> None:
    session = FakeSession(
        [FakeResponse(200, {"access_token": "test-token", "expires_in": 3600})]
    )
    provider = WclTokenProvider(
        "test-client-id",
        "test-client-secret",
        session=session,  # type: ignore[arg-type]
        clock=lambda: 100.0,
    )

    first_token = provider.get_access_token()
    second_token = provider.get_access_token()

    assert first_token == "test-token"
    assert second_token == "test-token"
    assert len(session.requests) == 1
    assert session.requests[0]["data"] == {"grant_type": "client_credentials"}
    assert session.requests[0]["auth"] == (
        "test-client-id",
        "test-client-secret",
    )


def test_invalidate_forces_new_token_request() -> None:
    session = FakeSession(
        [
            FakeResponse(200, {"access_token": "first-token", "expires_in": 3600}),
            FakeResponse(200, {"access_token": "second-token", "expires_in": 3600}),
        ]
    )
    provider = WclTokenProvider(
        "test-client-id",
        "test-client-secret",
        session=session,  # type: ignore[arg-type]
    )

    assert provider.get_access_token() == "first-token"
    provider.invalidate()
    assert provider.get_access_token() == "second-token"


def test_get_status_never_exposes_token_and_uses_monotonic_lifetime() -> None:
    session = FakeSession(
        [FakeResponse(200, {"access_token": "secret-token", "expires_in": 120})]
    )
    current_time = [1_000.0]
    provider = WclTokenProvider(
        "test-client-id",
        "test-client-secret",
        session=session,  # type: ignore[arg-type]
        clock=lambda: current_time[0],
        wall_clock=lambda: datetime(2026, 7, 30, 12, 0, tzinfo=UTC),
    )

    unavailable_status = provider.get_status()
    assert not unavailable_status.available
    assert unavailable_status.remaining_seconds is None

    provider.get_access_token()
    current_time[0] += 20
    available_status = provider.get_status()

    assert available_status.available
    assert available_status.remaining_seconds == 100
    assert available_status.expires_at == datetime(
        2026,
        7,
        30,
        12,
        1,
        40,
        tzinfo=UTC,
    )
    assert "secret-token" not in repr(available_status)

    provider.invalidate()
    assert not provider.get_status().available


def test_token_request_rejects_http_failure() -> None:
    session = FakeSession([FakeResponse(401, {"error": "invalid_client"})])
    provider = WclTokenProvider(
        "test-client-id",
        "test-client-secret",
        session=session,  # type: ignore[arg-type]
    )

    with pytest.raises(WclAuthenticationError, match="HTTP 401"):
        provider.get_access_token()


def test_from_environment_requires_credentials(monkeypatch) -> None:
    monkeypatch.delenv("WCL_CLIENT_ID", raising=False)
    monkeypatch.delenv("WCL_CLIENT_SECRET", raising=False)

    with pytest.raises(WclAuthenticationError, match="client ID"):
        WclTokenProvider.from_environment()
