"""Logging, identifier/URL validation, dedupe ring, and passive reply tracking."""

from collections import OrderedDict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import re
import time
from urllib.parse import urlparse

import anyio
from opsmesh.utils import logger_wrapper

from .exception import MediaError, QQAdapterException
from .typing import ADAPTER_NAME

log = logger_wrapper(ADAPTER_NAME)

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.:@+-]{1,256}$")
_ALLOWED_MEDIA_HOST_SUFFIXES = (
    ".qq.com",
    ".qpic.cn",
    ".qlogo.cn",
    ".myqcloud.com",
    ".gtimg.cn",
)

GROUP_PASSIVE_TTL_SECONDS = 300.0
GROUP_PASSIVE_MAX_REPLIES = 5
C2C_PASSIVE_TTL_SECONDS = 3600.0
C2C_PASSIVE_MAX_REPLIES = 4


def validate_qq_identifier(value: str, field_name: str = "id") -> str:
    """Validate an OpenID / GuildID / ChannelID before interpolating into a URL path."""
    if not value or ".." in value or "/" in value or "\\" in value:
        raise QQAdapterException(f"Invalid {field_name}: {value!r}")
    if not _SAFE_ID_RE.fullmatch(value):
        raise QQAdapterException(
            f"Invalid {field_name} format (must be 1..256 safe chars): {value!r}"
        )
    return value


def validate_media_url(url: str) -> str:
    """Ensure inbound attachment URLs are HTTPS on Tencent official media domains."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        raise MediaError(f"Refusing non-HTTPS media URL: {url!r}")
    if not any(
        host == suffix.lstrip(".") or host.endswith(suffix)
        for suffix in _ALLOWED_MEDIA_HOST_SUFFIXES
    ):
        raise MediaError(f"Refusing untrusted media host: {host!r}")
    return url


def derive_ed25519_seed(app_secret: str) -> bytes:
    """Derive 32-byte Ed25519 seed from QQ app_secret per Tencent Webhook spec."""
    raw = app_secret.encode("utf-8")
    if not raw:
        raise QQAdapterException("app_secret must not be empty.")
    while len(raw) < 32:
        raw += raw
    return raw[:32]


def format_iso8601_utc(value: datetime | timedelta) -> str:
    """Convert datetime or relative timedelta to timezone-aware ISO8601 string."""
    if isinstance(value, timedelta):
        target = datetime.now(tz=UTC) + value
    elif value.tzinfo is None:
        target = value.replace(tzinfo=UTC)
    else:
        target = value
    return target.isoformat()


class DedupeRing:
    """O(1) bounded LRU + TTL deduplication buffer for inbound events."""

    def __init__(self, *, capacity: int = 2048, ttl: float = 300.0) -> None:
        self._capacity = capacity
        self._ttl = ttl
        self._seen: OrderedDict[str, float] = OrderedDict()

    def seen_or_record(self, key: str) -> bool:
        """Return True if key was already seen within TTL; otherwise record it."""
        now = time.monotonic()
        self._evict_expired(now)
        if key in self._seen:
            self._seen.move_to_end(key)
            return True
        self._seen[key] = now + self._ttl
        while len(self._seen) > self._capacity:
            self._seen.popitem(last=False)
        return False

    def _evict_expired(self, now: float) -> None:
        while self._seen:
            oldest_key, expiry = next(iter(self._seen.items()))
            if expiry > now:
                break
            del self._seen[oldest_key]


@dataclass(slots=True)
class _PassiveSlot:
    expires_at: float
    max_replies: int
    next_seq: int = 1
    lock: anyio.Lock | None = None


class PassiveReplyTracker:
    """Track QQ v2 passive reply windows and allocate strictly increasing msg_seq."""

    def __init__(self, *, capacity: int = 4096) -> None:
        self._capacity = capacity
        self._slots: OrderedDict[str, _PassiveSlot] = OrderedDict()

    def register(
        self,
        msg_id: str,
        *,
        is_c2c: bool = False,
        ttl_seconds: float | None = None,
        max_replies: int | None = None,
    ) -> None:
        """Record an inbound message id eligible for passive replies."""
        if not msg_id:
            return
        ttl = (
            ttl_seconds
            if ttl_seconds is not None
            else (C2C_PASSIVE_TTL_SECONDS if is_c2c else GROUP_PASSIVE_TTL_SECONDS)
        )
        limit = (
            max_replies
            if max_replies is not None
            else (C2C_PASSIVE_MAX_REPLIES if is_c2c else GROUP_PASSIVE_MAX_REPLIES)
        )
        now = time.monotonic()
        self._evict_expired(now)
        self._slots[msg_id] = _PassiveSlot(
            expires_at=now + ttl,
            max_replies=limit,
            next_seq=1,
            lock=anyio.Lock(),
        )
        self._slots.move_to_end(msg_id)
        while len(self._slots) > self._capacity:
            self._slots.popitem(last=False)

    async def allocate_seq(self, msg_id: str, *, is_c2c: bool = False) -> int | None:
        """Return next strictly increasing msg_seq, or None if expired/exhausted."""
        if not msg_id:
            return None
        slot = self._slots.get(msg_id)
        if slot is None:
            self.register(msg_id, is_c2c=is_c2c)
            slot = self._slots[msg_id]
        if slot.lock is None:
            slot.lock = anyio.Lock()
        async with slot.lock:
            if time.monotonic() >= slot.expires_at or slot.next_seq > slot.max_replies:
                self._slots.pop(msg_id, None)
                return None
            seq = slot.next_seq
            slot.next_seq += 1
            return seq

    def _evict_expired(self, now: float) -> None:
        while self._slots:
            oldest_key, slot = next(iter(self._slots.items()))
            if slot.expires_at > now:
                break
            del self._slots[oldest_key]


__all__ = [
    "C2C_PASSIVE_MAX_REPLIES",
    "C2C_PASSIVE_TTL_SECONDS",
    "GROUP_PASSIVE_MAX_REPLIES",
    "GROUP_PASSIVE_TTL_SECONDS",
    "DedupeRing",
    "PassiveReplyTracker",
    "derive_ed25519_seed",
    "format_iso8601_utc",
    "log",
    "validate_media_url",
    "validate_qq_identifier",
]
