"""QQ Guild Core v1 APIs (guilds, channels, members, roles, channel permissions)."""

from typing import Any

from qq.config import BotConfig
from qq.typing import T_JsonDict
from qq.utils import validate_qq_identifier

from .client import ApiClient
from .token import TokenManager


class GuildCoreService:
    """Guild v1 core management endpoints."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    async def guilds(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        before: str | None = None,
        after: str | None = None,
        limit: int | None = None,
    ) -> Any:
        params: T_JsonDict = {}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if limit is not None:
            params["limit"] = limit
        return await self._client.request_json(
            "GET",
            "/users/@me/guilds",
            bot_config=bot_config,
            token_manager=token_manager,
            params=params or None,
        )

    async def get_guild(
        self, *, bot_config: BotConfig, token_manager: TokenManager, guild_id: str
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        return await self._client.request_json(
            "GET", f"/guilds/{gid}", bot_config=bot_config, token_manager=token_manager
        )

    async def get_channels(
        self, *, bot_config: BotConfig, token_manager: TokenManager, guild_id: str
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        return await self._client.request_json(
            "GET",
            f"/guilds/{gid}/channels",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def get_channel(
        self, *, bot_config: BotConfig, token_manager: TokenManager, channel_id: str
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        return await self._client.request_json(
            "GET",
            f"/channels/{cid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def post_channels(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        payload: T_JsonDict,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        return await self._client.request_json(
            "POST",
            f"/guilds/{gid}/channels",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def patch_channel(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        payload: T_JsonDict,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        return await self._client.request_json(
            "PATCH",
            f"/channels/{cid}",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def delete_channel(
        self, *, bot_config: BotConfig, token_manager: TokenManager, channel_id: str
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        return await self._client.request_json(
            "DELETE",
            f"/channels/{cid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def get_members(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        after: str | None = None,
        limit: int | None = None,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        params: T_JsonDict = {}
        if after:
            params["after"] = after
        if limit is not None:
            params["limit"] = limit
        return await self._client.request_json(
            "GET",
            f"/guilds/{gid}/members",
            bot_config=bot_config,
            token_manager=token_manager,
            params=params or None,
        )

    async def get_role_members(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        role_id: str,
        start_index: str | None = None,
        limit: int | None = None,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        rid = validate_qq_identifier(role_id, "role_id")
        params: T_JsonDict = {}
        if start_index:
            params["start_index"] = start_index
        if limit is not None:
            params["limit"] = limit
        return await self._client.request_json(
            "GET",
            f"/guilds/{gid}/roles/{rid}/members",
            bot_config=bot_config,
            token_manager=token_manager,
            params=params or None,
        )

    async def get_member(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        user_id: str,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        uid = validate_qq_identifier(user_id, "user_id")
        return await self._client.request_json(
            "GET",
            f"/guilds/{gid}/members/{uid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def delete_member(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        user_id: str,
        add_blacklist: bool = False,
        delete_history_msg_days: int = 0,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        uid = validate_qq_identifier(user_id, "user_id")
        return await self._client.request_json(
            "DELETE",
            f"/guilds/{gid}/members/{uid}",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body={
                "add_blacklist": add_blacklist,
                "delete_history_msg_days": delete_history_msg_days,
            },
        )

    async def get_guild_roles(
        self, *, bot_config: BotConfig, token_manager: TokenManager, guild_id: str
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        return await self._client.request_json(
            "GET",
            f"/guilds/{gid}/roles",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def post_guild_role(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        payload: T_JsonDict,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        return await self._client.request_json(
            "POST",
            f"/guilds/{gid}/roles",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def patch_guild_role(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        role_id: str,
        payload: T_JsonDict,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        rid = validate_qq_identifier(role_id, "role_id")
        return await self._client.request_json(
            "PATCH",
            f"/guilds/{gid}/roles/{rid}",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def delete_guild_role(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        role_id: str,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        rid = validate_qq_identifier(role_id, "role_id")
        return await self._client.request_json(
            "DELETE",
            f"/guilds/{gid}/roles/{rid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def put_guild_member_role(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        user_id: str,
        role_id: str,
        channel_id: str | None = None,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        uid = validate_qq_identifier(user_id, "user_id")
        rid = validate_qq_identifier(role_id, "role_id")
        body = {"channel": {"id": channel_id}} if channel_id else None
        return await self._client.request_json(
            "PUT",
            f"/guilds/{gid}/members/{uid}/roles/{rid}",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=body,
        )

    async def delete_guild_member_role(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        user_id: str,
        role_id: str,
        channel_id: str | None = None,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        uid = validate_qq_identifier(user_id, "user_id")
        rid = validate_qq_identifier(role_id, "role_id")
        body = {"channel": {"id": channel_id}} if channel_id else None
        return await self._client.request_json(
            "DELETE",
            f"/guilds/{gid}/members/{uid}/roles/{rid}",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=body,
        )

    async def get_channel_permissions(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        user_id: str,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        uid = validate_qq_identifier(user_id, "user_id")
        return await self._client.request_json(
            "GET",
            f"/channels/{cid}/members/{uid}/permissions",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def put_channel_permissions(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        user_id: str,
        payload: T_JsonDict,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        uid = validate_qq_identifier(user_id, "user_id")
        return await self._client.request_json(
            "PUT",
            f"/channels/{cid}/members/{uid}/permissions",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def get_channel_roles_permissions(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        role_id: str,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        rid = validate_qq_identifier(role_id, "role_id")
        return await self._client.request_json(
            "GET",
            f"/channels/{cid}/roles/{rid}/permissions",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def put_channel_roles_permissions(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        role_id: str,
        payload: T_JsonDict,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        rid = validate_qq_identifier(role_id, "role_id")
        return await self._client.request_json(
            "PUT",
            f"/channels/{cid}/roles/{rid}/permissions",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )


__all__ = ["GuildCoreService"]
