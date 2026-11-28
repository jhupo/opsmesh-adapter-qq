"""Declarative ActionDispatcher routing QQAction names to OpenAPI services."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import partial
from typing import Any

from qq.config import BotConfig
from qq.exception import ActionNotAvailable
from qq.typing import ADAPTER_NAME, QQAction, T_JsonDict

from .group_admin import GroupAdminService
from .guild_core import GuildCoreService
from .guild_ext import GuildExtService
from .guild_message import GuildMessageService
from .media import MediaService
from .messaging import MessagingService
from .token import TokenManager


@dataclass(slots=True, kw_only=True, frozen=True)
class ActionContext:
    """Execution context passed to registered QQ action handlers."""

    bot_config: BotConfig
    token_manager: TokenManager
    params: T_JsonDict


ActionHandler = Callable[[ActionContext], Awaitable[Any]]


def _bind(method: Callable[..., Awaitable[Any]]) -> ActionHandler:
    """Bind a service method accepting (bot_config, token_manager, **params)."""

    async def _handler(ctx: ActionContext) -> Any:
        return await method(
            bot_config=ctx.bot_config,
            token_manager=ctx.token_manager,
            **ctx.params,
        )

    return _handler


class ActionDispatcher:
    """Route QQAction enum members to domain OpenAPI services cleanly."""

    def __init__(
        self,
        *,
        messaging: MessagingService,
        media: MediaService,
        group_admin: GroupAdminService,
        guild_core: GuildCoreService,
        guild_message: GuildMessageService,
        guild_ext: GuildExtService,
    ) -> None:
        self._media = media
        self._handlers: dict[str, ActionHandler] = {}

        # Auto-bind all QQAction members whose names match domain service methods
        services = (messaging, group_admin, guild_core, guild_message, guild_ext)
        for action in QQAction:
            for svc in services:
                method = getattr(svc, action.value, None)
                if callable(method):
                    self._handlers[action] = _bind(method)
                    break

        # Explicit adapters for stream, token, and C2C/Group media actions
        self._handlers.update(
            {
                QQAction.GET_ACCESS_TOKEN: self._get_access_token,
                QQAction.SEND_GROUP_STREAM: _bind(messaging.send_stream_chunk),
                QQAction.SEND_C2C_STREAM: _bind(messaging.send_stream_chunk),
                QQAction.POST_C2C_FILES: partial(
                    self._post_files, is_c2c=True, id_key="openid"
                ),
                QQAction.POST_GROUP_FILES: partial(
                    self._post_files, is_c2c=False, id_key="group_openid"
                ),
                QQAction.POST_C2C_UPLOAD_PREPARE: partial(
                    self._upload_prepare, is_c2c=True, id_key="openid"
                ),
                QQAction.POST_GROUP_UPLOAD_PREPARE: partial(
                    self._upload_prepare, is_c2c=False, id_key="group_openid"
                ),
                QQAction.POST_C2C_UPLOAD_PART: self._put_upload_part,
                QQAction.POST_GROUP_UPLOAD_PART: self._put_upload_part,
                QQAction.POST_C2C_UPLOAD_FINISH: partial(
                    self._upload_finish, is_c2c=True, id_key="openid"
                ),
                QQAction.POST_GROUP_UPLOAD_FINISH: partial(
                    self._upload_finish, is_c2c=False, id_key="group_openid"
                ),
                QQAction.DOWNLOAD_ATTACHMENT: self._download_attachment,
            }
        )

    async def dispatch(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        action: str,
        params: T_JsonDict,
    ) -> Any:
        handler = self._handlers.get(action)
        if handler is None:
            raise ActionNotAvailable(ADAPTER_NAME, action)
        ctx = ActionContext(
            bot_config=bot_config, token_manager=token_manager, params=params
        )
        return await handler(ctx)

    async def _get_access_token(self, ctx: ActionContext) -> str:
        return await ctx.token_manager.get_token(
            force_refresh=bool(ctx.params.get("force_refresh", False))
        )

    async def _post_files(
        self, ctx: ActionContext, *, is_c2c: bool, id_key: str
    ) -> Any:
        return await self._media.post_files(
            bot_config=ctx.bot_config,
            token_manager=ctx.token_manager,
            target_id=ctx.params[id_key],
            is_c2c=is_c2c,
            file_type=ctx.params.get("file_type"),
            url=ctx.params.get("url"),
            file_data=ctx.params.get("file_data"),
            upload_id=ctx.params.get("upload_id"),
            srv_send_msg=bool(ctx.params.get("srv_send_msg", False)),
        )

    async def _upload_prepare(
        self, ctx: ActionContext, *, is_c2c: bool, id_key: str
    ) -> Any:
        return await self._media.upload_prepare(
            bot_config=ctx.bot_config,
            token_manager=ctx.token_manager,
            target_id=ctx.params[id_key],
            is_c2c=is_c2c,
            file_type=ctx.params["file_type"],
            file_name=ctx.params["file_name"],
            file_size=int(ctx.params["file_size"]),
            md5_hex=ctx.params["md5_hex"],
            sha1_hex=ctx.params["sha1_hex"],
            md5_10m_hex=ctx.params.get("md5_10m_hex"),
        )

    async def _put_upload_part(self, ctx: ActionContext) -> str:
        return await self._media.put_upload_part(
            presigned_url=ctx.params["presigned_url"],
            chunk=ctx.params["chunk"],
        )

    async def _upload_finish(
        self, ctx: ActionContext, *, is_c2c: bool, id_key: str
    ) -> Any:
        return await self._media.upload_part_finish(
            bot_config=ctx.bot_config,
            token_manager=ctx.token_manager,
            target_id=ctx.params[id_key],
            is_c2c=is_c2c,
            upload_id=ctx.params["upload_id"],
            part_index=int(ctx.params["part_index"]),
            block_size=int(ctx.params["block_size"]),
            md5_hex=ctx.params["md5_hex"],
        )

    async def _download_attachment(self, ctx: ActionContext) -> bytes:
        return await self._media.download_attachment(
            url=ctx.params["url"], max_bytes=ctx.params.get("max_bytes")
        )


__all__ = ["ActionContext", "ActionDispatcher", "ActionHandler"]
