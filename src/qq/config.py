"""Pydantic v2 configuration models for QQ Official Bot adapter."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from .typing import QQ_API_BASE, QQ_SANDBOX_API_BASE, Intents


class IntentConfig(BaseModel):
    """Boolean intent toggles converted to QQ Gateway bitmask."""

    model_config = ConfigDict(extra="ignore")

    guilds: bool = True
    guild_members: bool = True
    guild_messages: bool = False
    guild_message_reactions: bool = True
    direct_message: bool = True
    open_forums_event: bool = False
    audio_or_live_channel_member: bool = False
    c2c_group_at_messages: bool = True
    interaction: bool = True
    message_audit: bool = True
    forum_event: bool = False
    audio_action: bool = False
    public_guild_messages: bool = True

    def to_int(self) -> int:
        mask = Intents(0)
        for flag in Intents:
            if getattr(self, flag.name.lower(), False):
                mask |= flag
        return int(mask)


class BotConfig(BaseModel):
    """Per-bot credential and transport configuration."""

    model_config = ConfigDict(extra="ignore")

    app_id: str = Field(min_length=1)
    app_secret: SecretStr
    transport: Literal["websocket", "webhook"] = "websocket"
    is_sandbox: bool = False
    intent: IntentConfig = Field(default_factory=IntentConfig)
    shard: tuple[int, int] | None = None
    auto_markdown: bool = False

    @field_validator("shard")
    @classmethod
    def _validate_shard(cls, value: tuple[int, int] | None) -> tuple[int, int] | None:
        if value is not None:
            shard_id, total_shards = value
            if total_shards <= 0 or not (0 <= shard_id < total_shards):
                raise ValueError(f"Invalid shard specification: {value!r}")
        return value

    @property
    def gateway_id(self) -> str:
        return f"qq:{self.app_id}"

    @property
    def api_base(self) -> str:
        return QQ_SANDBOX_API_BASE if self.is_sandbox else QQ_API_BASE


class Config(BaseModel):
    """Global QQ Official Bot adapter settings (loaded from OpsMesh Driver config)."""

    model_config = ConfigDict(extra="ignore")

    qq_bots: list[BotConfig] = Field(default_factory=list)
    qq_is_sandbox: bool = False
    qq_webhook_path: str = "/qq/webhook"
    qq_timeout: float = Field(default=30.0, gt=0)
    qq_dedupe_capacity: int = Field(default=2048, ge=64)
    qq_dedupe_ttl: float = Field(default=300.0, gt=0)
    qq_bdh_threshold_bytes: int = Field(default=2 * 1024 * 1024, ge=65536)
    qq_bdh_concurrency: int = Field(default=4, ge=1, le=16)
    qq_max_media_download_bytes: int = Field(default=100 * 1024 * 1024, ge=1024)
    qq_webhook_max_body_bytes: int = Field(default=1024 * 1024, ge=1024)


__all__ = ["BotConfig", "Config", "IntentConfig"]
