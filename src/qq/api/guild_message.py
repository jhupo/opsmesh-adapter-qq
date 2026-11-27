"""QQ Guild v1 channel messages, DMS, reactions, pins, and announces APIs."""

from typing import Any

from qq.config import BotConfig
from qq.typing import T_JsonDict
from qq.utils import validate_qq_identifier

from .client import ApiClient
from .token import TokenManager


class GuildMessageService:
    """Guild v1 messaging, DMS, reaction, pin, and announcement endpoints."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    async def get_message_of_id(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        message_id: str,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        mid = validate_qq_identifier(message_id, "message_id")
        return await self._client.request_json(
            "GET",
            f"/channels/{cid}/messages/{mid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def post_messages(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        payload: T_JsonDict,
        file_image: tuple[str, bytes] | None = None,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        if file_image is not None:
            return await self._client.request_json(
                "POST",
                f"/channels/{cid}/messages",
                bot_config=bot_config,
                token_manager=token_manager,
                data={k: str(v) for k, v in payload.items() if v is not None},
                files={"file_image": file_image},
            )
        return await self._client.request_json(
            "POST",
            f"/channels/{cid}/messages",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def delete_message(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        message_id: str,
        hidetip: bool = False,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        mid = validate_qq_identifier(message_id, "message_id")
        return await self._client.request_json(
            "DELETE",
            f"/channels/{cid}/messages/{mid}",
            bot_config=bot_config,
            token_manager=token_manager,
            params={"hidetip": str(hidetip).lower()},
        )

    async def get_message_setting(
        self, *, bot_config: BotConfig, token_manager: TokenManager, guild_id: str
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        return await self._client.request_json(
            "GET",
            f"/guilds/{gid}/message/setting",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def post_dms(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        recipient_id: str,
        source_guild_id: str,
    ) -> Any:
        return await self._client.request_json(
            "POST",
            "/users/@me/dms",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body={
                "recipient_id": recipient_id,
                "source_guild_id": source_guild_id,
            },
        )

    async def post_dms_messages(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        payload: T_JsonDict,
        file_image: tuple[str, bytes] | None = None,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        if file_image is not None:
            return await self._client.request_json(
                "POST",
                f"/dms/{gid}/messages",
                bot_config=bot_config,
                token_manager=token_manager,
                data={k: str(v) for k, v in payload.items() if v is not None},
                files={"file_image": file_image},
            )
        return await self._client.request_json(
            "POST",
            f"/dms/{gid}/messages",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def delete_dms_message(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        message_id: str,
        hidetip: bool = False,
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        mid = validate_qq_identifier(message_id, "message_id")
        return await self._client.request_json(
            "DELETE",
            f"/dms/{gid}/messages/{mid}",
            bot_config=bot_config,
            token_manager=token_manager,
            params={"hidetip": str(hidetip).lower()},
        )

    async def put_message_reaction(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        message_id: str,
        emoji_type: int,
        emoji_id: str,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        mid = validate_qq_identifier(message_id, "message_id")
        eid = validate_qq_identifier(emoji_id, "emoji_id")
        return await self._client.request_json(
            "PUT",
            f"/channels/{cid}/messages/{mid}/reactions/{emoji_type}/{eid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def delete_own_message_reaction(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        message_id: str,
        emoji_type: int,
        emoji_id: str,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        mid = validate_qq_identifier(message_id, "message_id")
        eid = validate_qq_identifier(emoji_id, "emoji_id")
        return await self._client.request_json(
            "DELETE",
            f"/channels/{cid}/messages/{mid}/reactions/{emoji_type}/{eid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def get_reaction_users(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        message_id: str,
        emoji_type: int,
        emoji_id: str,
        cookie: str | None = None,
        limit: int | None = None,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        mid = validate_qq_identifier(message_id, "message_id")
        eid = validate_qq_identifier(emoji_id, "emoji_id")
        params: T_JsonDict = {}
        if cookie:
            params["cookie"] = cookie
        if limit is not None:
            params["limit"] = limit
        return await self._client.request_json(
            "GET",
            f"/channels/{cid}/messages/{mid}/reactions/{emoji_type}/{eid}",
            bot_config=bot_config,
            token_manager=token_manager,
            params=params or None,
        )

    async def put_pins_message(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        message_id: str,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        mid = validate_qq_identifier(message_id, "message_id")
        return await self._client.request_json(
            "PUT",
            f"/channels/{cid}/pins/{mid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def delete_pins_message(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        channel_id: str,
        message_id: str,
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        mid = validate_qq_identifier(message_id, "message_id")
        return await self._client.request_json(
            "DELETE",
            f"/channels/{cid}/pins/{mid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def get_pins_message(
        self, *, bot_config: BotConfig, token_manager: TokenManager, channel_id: str
    ) -> Any:
        cid = validate_qq_identifier(channel_id, "channel_id")
        return await self._client.request_json(
            "GET",
            f"/channels/{cid}/pins",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def post_guild_announces(
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
            f"/guilds/{gid}/announces",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )

    async def delete_guild_announces(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        guild_id: str,
        message_id: str = "all",
    ) -> Any:
        gid = validate_qq_identifier(guild_id, "guild_id")
        mid = validate_qq_identifier(message_id, "message_id")
        return await self._client.request_json(
            "DELETE",
            f"/guilds/{gid}/announces/{mid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )


__all__ = ["GuildMessageService"]
