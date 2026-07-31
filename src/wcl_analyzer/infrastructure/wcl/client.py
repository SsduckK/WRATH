"""HTTP GraphQL client for the Warcraft Logs public API."""

from collections.abc import Callable, Mapping
from time import sleep
from typing import Protocol

import requests

WCL_PUBLIC_API_URL = "https://www.warcraftlogs.com/api/v2/client"


class TokenProvider(Protocol):
    """Token capability required by the GraphQL client."""

    def get_access_token(self) -> str:
        """Return a usable access token."""
        ...

    def invalidate(self) -> None:
        """Discard the current token."""
        ...


class WclClientError(RuntimeError):
    """Base error for WCL GraphQL requests."""


class WclNetworkError(WclClientError):
    """Raised when WCL cannot be reached after limited retries."""


class WclGraphqlError(WclClientError):
    """Raised when a successful HTTP response contains GraphQL errors."""


class WclRateLimitError(WclClientError):
    """Raised when WCL rejects a request due to rate limiting."""

    def __init__(self, retry_after: str | None) -> None:
        self.retry_after = retry_after
        message = "WCL rate limit exceeded"
        if retry_after:
            message = f"{message}; retry after {retry_after} seconds"
        super().__init__(message)


class WclGraphqlClient:
    """Execute authenticated GraphQL requests against the WCL public API."""

    def __init__(
        self,
        token_provider: TokenProvider,
        *,
        session: requests.Session | None = None,
        api_url: str = WCL_PUBLIC_API_URL,
        timeout_seconds: float = 20.0,
        max_retries: int = 2,
        sleeper: Callable[[float], None] = sleep,
    ) -> None:
        self._token_provider = token_provider
        self._session = session or requests.Session()
        self._api_url = api_url
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._sleeper = sleeper

    def execute(
        self,
        *,
        query: str,
        variables: Mapping[str, object],
    ) -> Mapping[str, object]:
        """Execute a query, refreshing authentication once on HTTP 401."""
        response = self._send(query, variables)
        if response.status_code == 401:
            self._token_provider.invalidate()
            response = self._send(query, variables)

        if response.status_code == 401:
            raise WclClientError("WCL authentication failed after token refresh")
        if response.status_code == 429:
            raise WclRateLimitError(response.headers.get("Retry-After"))
        if not 200 <= response.status_code < 300:
            raise WclClientError(
                f"WCL GraphQL request failed with HTTP {response.status_code}"
            )

        payload = self._decode_response(response)
        errors = payload.get("errors")
        if errors:
            raise WclGraphqlError(self._format_graphql_errors(errors))
        return payload

    @staticmethod
    def _format_graphql_errors(errors: object) -> str:
        """Expose safe GraphQL messages without logging request credentials."""
        messages: list[str] = []
        if isinstance(errors, list):
            for error in errors:
                if isinstance(error, Mapping):
                    message = error.get("message")
                    if isinstance(message, str) and message.strip():
                        messages.append(message.strip())
        detail = "; ".join(messages)
        return (
            f"WCL GraphQL response contains errors: {detail}"
            if detail
            else "WCL GraphQL response contains errors"
        )

    def _send(
        self,
        query: str,
        variables: Mapping[str, object],
    ) -> requests.Response:
        for attempt in range(self._max_retries + 1):
            token = self._token_provider.get_access_token()
            try:
                response = self._session.post(
                    self._api_url,
                    json={"query": query, "variables": dict(variables)},
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json",
                    },
                    timeout=self._timeout_seconds,
                )
            except (requests.Timeout, requests.ConnectionError) as error:
                if attempt == self._max_retries:
                    raise WclNetworkError(
                        "could not connect to the WCL GraphQL API"
                    ) from error
                self._sleeper(2**attempt)
                continue

            if response.status_code >= 500 and attempt < self._max_retries:
                self._sleeper(2**attempt)
                continue
            return response

        raise AssertionError("unreachable WCL retry state")

    @staticmethod
    def _decode_response(response: requests.Response) -> Mapping[str, object]:
        try:
            payload = response.json()
        except requests.exceptions.JSONDecodeError as error:
            raise WclClientError("WCL GraphQL response is not valid JSON") from error
        if not isinstance(payload, Mapping):
            raise WclClientError("WCL GraphQL response must be a JSON object")
        return payload
