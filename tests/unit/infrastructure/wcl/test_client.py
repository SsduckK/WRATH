"""Tests for authenticated WCL GraphQL HTTP requests."""

from collections.abc import Mapping

import pytest

from wcl_analyzer.infrastructure.wcl.client import (
    WclGraphqlClient,
    WclGraphqlError,
    WclRateLimitError,
)


class FakeResponse:
    """Small response double for GraphQL client tests."""

    def __init__(
        self,
        status_code: int,
        payload: Mapping[str, object],
        *,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self) -> Mapping[str, object]:
        return self._payload


class FakeSession:
    """Return queued GraphQL responses and record each request."""

    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses = responses
        self.requests: list[dict[str, object]] = []

    def post(self, url: str, **kwargs: object) -> FakeResponse:
        self.requests.append({"url": url, **kwargs})
        return self._responses.pop(0)


class FakeTokenProvider:
    """Provide a changed token after invalidation."""

    def __init__(self) -> None:
        self.invalidations = 0

    def get_access_token(self) -> str:
        return "new-token" if self.invalidations else "old-token"

    def invalidate(self) -> None:
        self.invalidations += 1


def test_execute_posts_query_and_variables_with_bearer_token() -> None:
    payload = {"data": {"reportData": {"report": {}}}}
    session = FakeSession([FakeResponse(200, payload)])
    provider = FakeTokenProvider()
    client = WclGraphqlClient(
        provider,
        session=session,  # type: ignore[arg-type]
    )

    result = client.execute(query="query Test {}", variables={"code": "ABC"})

    assert result == payload
    assert session.requests[0]["json"] == {
        "query": "query Test {}",
        "variables": {"code": "ABC"},
    }
    assert session.requests[0]["headers"] == {
        "Authorization": "Bearer old-token",
        "Accept": "application/json",
    }


def test_execute_refreshes_token_once_after_http_401() -> None:
    payload = {"data": {"reportData": {"report": {}}}}
    session = FakeSession(
        [
            FakeResponse(401, {"error": "unauthorized"}),
            FakeResponse(200, payload),
        ]
    )
    provider = FakeTokenProvider()
    client = WclGraphqlClient(
        provider,
        session=session,  # type: ignore[arg-type]
    )

    assert client.execute(query="query Test {}", variables={}) == payload
    assert provider.invalidations == 1
    assert session.requests[0]["headers"]["Authorization"] == "Bearer old-token"  # type: ignore[index]
    assert session.requests[1]["headers"]["Authorization"] == "Bearer new-token"  # type: ignore[index]


def test_execute_rejects_graphql_errors_on_http_200() -> None:
    session = FakeSession(
        [FakeResponse(200, {"errors": [{"message": "Report not found"}]})]
    )
    client = WclGraphqlClient(
        FakeTokenProvider(),
        session=session,  # type: ignore[arg-type]
    )

    with pytest.raises(WclGraphqlError, match="contains errors"):
        client.execute(query="query Test {}", variables={})


def test_execute_exposes_retry_after_on_http_429() -> None:
    session = FakeSession(
        [
            FakeResponse(
                429,
                {"error": "rate_limited"},
                headers={"Retry-After": "60"},
            )
        ]
    )
    client = WclGraphqlClient(
        FakeTokenProvider(),
        session=session,  # type: ignore[arg-type]
    )

    with pytest.raises(WclRateLimitError) as error:
        client.execute(query="query Test {}", variables={})

    assert error.value.retry_after == "60"
