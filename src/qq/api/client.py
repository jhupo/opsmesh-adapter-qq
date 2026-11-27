"""Unified authenticated HTTP client for QQ OpenAPI v1/v2."""

import json
from typing import TYPE_CHECKING, Any, NoReturn

from opsmesh.drivers import Request

from qq.config import BotConfig, Config
from qq.exception import (
    AuditException,
    QQActionFailed,
    QQNetworkError,
    RateLimitException,
    UnauthorizedException,
)
from qq.typing import T_JsonDict

if TYPE_CHECKING:
    from qq.adapter import Adapter
    from qq.api.token import TokenManager

_AUDIT_CODES = frozenset({304023, 304024})
_STATUS_EXC_MAP: dict[int, type[QQActionFailed]] = {
    401: UnauthorizedException,
    429: RateLimitException,
}


class ApiClient:
    """Execute authenticated QQ OpenAPI HTTP requests with standard error mapping."""

    def __init__(self, adapter: "Adapter", config: Config) -> None:
        self._adapter = adapter
        self._config = config

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        bot_config: BotConfig,
        token_manager: "TokenManager",
        params: T_JsonDict | None = None,
        json_body: Any = None,
        files: Any = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
        retry_on_401: bool = True,
    ) -> Any:
        """Send an authenticated request to QQ OpenAPI and parse JSON response."""
        token = await token_manager.get_token()
        url = (
            path
            if path.startswith(("http://", "https://"))
            else f"{bot_config.api_base}{path}"
        )
        req_headers = {
            "Authorization": f"QQBot {token}",
            "X-Union-Appid": bot_config.app_id,
            **(headers or {}),
        }
        req = Request(
            method,
            url,
            params=params,
            json=json_body,
            files=files,
            data=data,
            headers=req_headers,
            timeout=self._config.qq_timeout,
        )
        try:
            resp = await self._adapter.request(req)
        except Exception as exc:
            raise QQNetworkError(f"QQ API {method} {path} failed: {exc}") from exc

        if resp.status_code == 401 and retry_on_401:
            await token_manager.get_token(force_refresh=True)
            return await self.request_json(
                method,
                path,
                bot_config=bot_config,
                token_manager=token_manager,
                params=params,
                json_body=json_body,
                files=files,
                data=data,
                headers=headers,
                retry_on_401=False,
            )

        parsed = self._decode_body(resp.content)
        if 200 <= resp.status_code < 300:
            return parsed

        trace_id = resp.headers.get("X-Tps-trace-ID") or resp.headers.get(
            "x-tps-trace-id"
        )
        self._raise_api_error(resp.status_code, parsed, trace_id)

    @staticmethod
    def _raise_api_error(
        status_code: int, parsed: Any, trace_id: str | None
    ) -> NoReturn:
        body = parsed if isinstance(parsed, dict) else {}
        code = body.get("code")
        err_code = body.get("err_code")
        msg = str(body.get("message") or f"HTTP {status_code}")
        exc_cls = (
            AuditException
            if code in _AUDIT_CODES
            else _STATUS_EXC_MAP.get(status_code, QQActionFailed)
        )
        raise exc_cls(
            msg,
            status_code=status_code,
            code=code,
            err_code=err_code,
            trace_id=trace_id,
            data=parsed,
        )

    @staticmethod
    def _decode_body(content: str | bytes | None) -> Any:
        if not content:
            return None
        text = (
            content.decode("utf-8", errors="replace")
            if isinstance(content, (bytes, bytearray))
            else str(content)
        ).strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}


__all__ = ["ApiClient"]
