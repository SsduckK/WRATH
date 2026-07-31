"""OAuth client-credentials authentication for the WCL public API."""

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from time import monotonic

import requests

from wcl_analyzer.app import TokenStatus

WCL_TOKEN_URL = "https://www.warcraftlogs.com/oauth/token"
TOKEN_REFRESH_MARGIN_SECONDS = 30.0


class WclAuthenticationError(RuntimeError):
    """Raised when WCL credentials or token issuance are invalid."""


@dataclass(frozen=True, slots=True)
class AccessToken:
    """An access token and its monotonic expiration deadline."""

    value: str
    expires_at: float


class WclTokenProvider:
    """Issue and cache WCL client-credentials access tokens."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        session: requests.Session | None = None,
        token_url: str = WCL_TOKEN_URL,
        timeout_seconds: float = 10.0,
        clock: Callable[[], float] = monotonic,
        wall_clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if not client_id:
            raise WclAuthenticationError("WCL client ID is not configured")
        if not client_secret:
            raise WclAuthenticationError("WCL client secret is not configured")

        self._client_id = client_id
        self._client_secret = client_secret
        self._session = session or requests.Session()
        self._token_url = token_url
        self._timeout_seconds = timeout_seconds
        self._clock = clock
        self._wall_clock = wall_clock
        self._cached_token: AccessToken | None = None

    @classmethod
    def from_environment(
        cls,
        *,
        session: requests.Session | None = None,
    ) -> "WclTokenProvider":
        """Create a provider from WCL_CLIENT_ID and WCL_CLIENT_SECRET."""
        return cls(
            client_id=os.getenv("WCL_CLIENT_ID", ""),
            client_secret=os.getenv("WCL_CLIENT_SECRET", ""),
            session=session,
        )

    def get_access_token(self) -> str:
        """Return a cached token or obtain a new one from WCL."""
        if self._is_cached_token_valid():
            assert self._cached_token is not None
            return self._cached_token.value

        try:
            response = self._session.post(
                self._token_url,
                data={"grant_type": "client_credentials"},
                auth=(self._client_id, self._client_secret),
                timeout=self._timeout_seconds,
            )
        except requests.RequestException as error:
            raise WclAuthenticationError(
                "could not connect to the WCL token endpoint"
            ) from error

        if response.status_code != 200:
            raise WclAuthenticationError(
                f"WCL token request failed with HTTP {response.status_code}"
            )

        payload = _response_mapping(response)
        token_value = payload.get("access_token")
        expires_in = payload.get("expires_in")
        if not isinstance(token_value, str) or not token_value:
            raise WclAuthenticationError("WCL token response is missing access_token")
        if (
            isinstance(expires_in, bool)
            or not isinstance(expires_in, int | float)
            or expires_in <= 0
        ):
            raise WclAuthenticationError("WCL token response has invalid expires_in")

        self._cached_token = AccessToken(
            value=token_value,
            expires_at=self._clock() + float(expires_in),
        )
        return token_value

    def invalidate(self) -> None:
        """Discard the cached token, normally after an HTTP 401 response."""
        self._cached_token = None

    def get_status(self) -> TokenStatus:
        """Return token lifetime metadata without exposing the token value."""
        token = self._cached_token
        if token is None:
            return TokenStatus(
                available=False,
                expires_at=None,
                remaining_seconds=None,
            )

        remaining_seconds = max(0, int(token.expires_at - self._clock()))
        return TokenStatus(
            available=remaining_seconds > TOKEN_REFRESH_MARGIN_SECONDS,
            expires_at=self._wall_clock() + timedelta(seconds=remaining_seconds),
            remaining_seconds=remaining_seconds,
        )

    def _is_cached_token_valid(self) -> bool:
        token = self._cached_token
        if token is None:
            return False
        return self._clock() < token.expires_at - TOKEN_REFRESH_MARGIN_SECONDS


def _response_mapping(response: requests.Response) -> Mapping[str, object]:
    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError as error:
        raise WclAuthenticationError("WCL token response is not valid JSON") from error
    if not isinstance(payload, Mapping):
        raise WclAuthenticationError("WCL token response must be a JSON object")
    return payload
