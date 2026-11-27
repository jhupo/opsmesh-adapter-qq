"""Single-flight AppAccessToken manager for QQ Official Bot."""

import json
import time
from typing import TYPE_CHECKING

import anyio
from opsmesh.drivers import Request

from qq.config import BotConfig
from qq.exception import QQNetworkError, TokenError
from qq.typing import QQ_AUTH_URL

if TYPE_CHECKING:
    from qq.adapter import Adapter

_REFRESH_MARGIN_SECONDS = 60.0


class TokenManager:
    """Acquire and cache QQ AppAccessToken with single-flight refresh."""

    def __init__(
        self,
        adapter: "Adapter",
        bot_config: BotConfig,
        *,
        timeout: float = 30.0,
    ) -> None:
        self._adapter = adapter
        self._bot_config = bot_config
        self._timeout = timeout
        self._lock = anyio.Lock()
        self._token: str | None = None
        self._expires_at: float = 0.0

    async def get_token(self, *, force_refresh: bool = False) -> str:
        """Return a valid AppAccessToken, refreshing when expired or forced."""
        now = time.monotonic()
        if not force_refresh and self._token and now < self._expires_at:
            return self._token

        async with self._lock:
            now = time.monotonic()
            if not force_refresh and self._token and now < self._expires_at:
                return self._token

            req = Request(
                "POST",
                QQ_AUTH_URL,
                json={
                    "appId": self._bot_config.app_id,
                    "clientSecret": self._bot_config.app_secret.get_secret_value(),
                },
                timeout=self._timeout,
            )
            try:
                resp = await self._adapter.request(req)
            except Exception as exc:
                raise QQNetworkError(
                    f"Failed to request QQ access token: {exc}"
                ) from exc

            if resp.status_code != 200 or not resp.content:
                raise TokenError(
                    f"QQ token endpoint returned HTTP {resp.status_code}",
                    status_code=resp.status_code,
                )

            data = json.loads(
                resp.content.decode("utf-8")
                if isinstance(resp.content, (bytes, bytearray))
                else str(resp.content)
            )
            token = data.get("access_token")
            expires_in = int(data.get("expires_in", 0) or 0)
            if not isinstance(token, str) or not token:
                raise TokenError(
                    f"QQ token response missing access_token: {data}",
                    status_code=resp.status_code,
                    code=data.get("code"),
                )

            self._token = token
            self._expires_at = time.monotonic() + max(
                expires_in - _REFRESH_MARGIN_SECONDS, 30.0
            )
            return token


__all__ = ["TokenManager"]
