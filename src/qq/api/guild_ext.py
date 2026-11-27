"""QQ Guild v1 extended APIs (mute, schedules, audio/mic, threads, permissions)."""

from typing import Any

from qq.config import BotConfig
from qq.typing import T_JsonDict
from qq.utils import validate_qq_identifier

from .client import ApiClient
from .token import TokenManager


class GuildExtService:
    """Guild v1 mute, schedule, audio, forum thread, and API permission endpoints."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    async def patch_guild_mute(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        payload: T_JsonDict,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        return await self._client.request_json(
            "PATCH",
            f"/guilds/{gid}/mute",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def patch_guild_member_mute(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        user_id: str,
        payload: T_JsonDict,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        uid = validate_qq_identifier(user_id, "user_id")
        return await self._client.request_json(
            "PATCH",
            f"/guilds/{gid}/members/{uid}/mute",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def patch_guild_mute_multi_member(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        payload: T_JsonDict,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        return await self._client.request_json(
            "PATCH",
            f"/guilds/{gid}/mute",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def get_schedules(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        since: int | None = None,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        params = {"since": since} if since is not None else None
        return await self._client.request_json(
            "GET",
            f"/channels/{cid}/schedules",
            bot_config=bot_config,
            token_manager=token_manager,
            params=params,
        )

    async def get_schedule(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        schedule_id: str,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        sid = validate_qq_identifier(schedule_id, "schedule_id")
        return await self._client.request_json(
            "GET",
            f"/channels/{cid}/schedules/{sid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def post_schedule(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        payload: T_JsonDict,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        return await self._client.request_json(
            "POST",
            f"/channels/{cid}/schedules",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def patch_schedule(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        schedule_id: str,
        payload: T_JsonDict,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        sid = validate_qq_identifier(schedule_id, "schedule_id")
        return await self._client.request_json(
            "PATCH",
            f"/channels/{cid}/schedules/{sid}",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def delete_schedule(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        schedule_id: str,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        sid = validate_qq_identifier(schedule_id, "schedule_id")
        return await self._client.request_json(
            "DELETE",
            f"/channels/{cid}/schedules/{sid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def audio_control(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        payload: T_JsonDict,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        return await self._client.request_json(
            "POST",
            f"/channels/{cid}/audio",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def put_mic(
        self, *, bot_config: BotConfig, token_manager: TokenManager, channel_id: str
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        return await self._client.request_json(
            "PUT",
            f"/channels/{cid}/mic",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def delete_mic(
        self, *, bot_config: BotConfig, token_manager: TokenManager, channel_id: str
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        return await self._client.request_json(
            "DELETE",
            f"/channels/{cid}/mic",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def get_threads_list(
        self, *, bot_config: BotConfig, token_manager: TokenManager, channel_id: str
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        return await self._client.request_json(
            "GET",
            f"/channels/{cid}/threads",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def get_thread(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        thread_id: str,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        tid = validate_qq_identifier(thread_id, "thread_id")
        return await self._client.request_json(
            "GET",
            f"/channels/{cid}/threads/{tid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def put_thread(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        payload: T_JsonDict,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        return await self._client.request_json(
            "PUT",
            f"/channels/{cid}/threads",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def delete_thread(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        thread_id: str,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        tid = validate_qq_identifier(thread_id, "thread_id")
        return await self._client.request_json(
            "DELETE",
            f"/channels/{cid}/threads/{tid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def get_guild_api_permission(
        self, *, bot_config: BotConfig, token_manager: TokenManager, guild_id: str
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        return await self._client.request_json(
            "GET",
            f"/guilds/{gid}/api_permission",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def post_api_permission_demand(
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
            f"/guilds/{gid}/api_permission/demand",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )


__all__ = ["GuildExtService"]
