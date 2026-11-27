"""Exception hierarchy inheriting directly from opsmesh.exception primitives."""

from typing import Any

from opsmesh.exception import (
    ActionFailed,
    ActionNotAvailable,
    AdapterException,
    NetworkError,
    NoLogException,
)

from .typing import ADAPTER_NAME


class QQAdapterException(AdapterException):
    """Base exception for all QQ Official Bot adapter errors."""

    def __init__(self, message: str = "") -> None:
        super().__init__(ADAPTER_NAME, message)
        self.message: str = message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r})"


class QQNetworkError(QQAdapterException, NetworkError):
    """HTTP or WebSocket transport failure communicating with QQ Open Platform."""


class QQActionFailed(QQAdapterException, ActionFailed):
    """QQ OpenAPI returned a non-2xx HTTP status or non-zero platform error code."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: int | str | None = None,
        err_code: int | None = None,
        trace_id: str | None = None,
        data: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code: int | None = status_code
        self.code: int | str | None = code
        self.err_code: int | None = err_code
        self.trace_id: str | None = trace_id
        self.data: Any = data

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"status_code={self.status_code!r}, "
            f"code={self.code!r}, "
            f"err_code={self.err_code!r}, "
            f"message={self.message!r}, "
            f"trace_id={self.trace_id!r})"
        )


class UnauthorizedException(QQActionFailed):
    """HTTP 401 or invalid AppAccessToken."""


class RateLimitException(QQActionFailed):
    """HTTP 429 rate-limit response from QQ OpenAPI."""


class AuditException(QQActionFailed):
    """Message accepted asynchronously for platform content audit (304023/304024)."""


class TokenError(QQActionFailed):
    """Failed to acquire or refresh AppAccessToken from bots.qq.com."""


class WebhookVerificationError(QQAdapterException):
    """Invalid Ed25519 signature, missing headers, or oversized Webhook request."""


class MediaError(QQAdapterException):
    """Rich media upload, BDH chunking, SSRF guard, or attachment download error."""


class MediaLimitExceeded(MediaError):
    """Attachment size exceeds configured limit."""

    def __init__(
        self,
        message: str,
        *,
        limit_bytes: int,
        actual_bytes: int | None = None,
    ) -> None:
        super().__init__(message)
        self.limit_bytes: int = limit_bytes
        self.actual_bytes: int | None = actual_bytes


__all__ = [
    "ActionNotAvailable",
    "AuditException",
    "MediaError",
    "MediaLimitExceeded",
    "NoLogException",
    "QQActionFailed",
    "QQAdapterException",
    "QQNetworkError",
    "RateLimitException",
    "TokenError",
    "UnauthorizedException",
    "WebhookVerificationError",
]
