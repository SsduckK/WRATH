"""Tests for WCL client-credentials token handling."""

from collections.abc import Mapping

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
