"""C2C & Group v2 messaging, gateway discovery, interaction ACK, and MessageStream."""

from types import TracebackType
from typing import TYPE_CHECKING, Any, Self

from qq.config import BotConfig
from qq.event.models import (
    PostC2CMessagesReturn,
    PostGroupMessagesReturn,
    ShardGatewayReturn,
    User,
)
from qq.typing import QQMsgType, StreamState, T_JsonDict
from qq.utils import validate_qq_identifier

from .client import ApiClient
from .token import TokenManager

if TYPE_CHECKING:
    from qq.gateway import Gateway


class MessagingService:
    """QQ v2 Group/C2C messaging, stream replies, gateway URLs, and interactions."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    async def me(self, *, bot_config: BotConfig, token_manager: TokenManager) -> User:
        data = await self._client.request_json(
            "GET", "/users/@me", bot_config=bot_config, token_manager=token_manager
        )
        return User.model_validate(data or {})

    async def url_get(
        self, *, bot_config: BotConfig, token_manager: TokenManager
    ) -> str:
        data = await self._client.request_json(
            "GET", "/gateway", bot_config=bot_config, token_manager=token_manager
        )
        return str((data or {}).get("url", ""))

    async def shard_url_get(
        self, *, bot_config: BotConfig, token_manager: TokenManager
    ) -> ShardGatewayReturn:
        data = await self._client.request_json(
            "GET", "/gateway/bot", bot_config=bot_config, token_manager=token_manager
        )
        return ShardGatewayReturn.model_validate(data or {})

    async def put_interaction(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        interaction_id: str,
        code: int = 0,
    ) -> None:
        safe_id = validate_qq_identifier(interaction_id, "interaction_id")
        await self._client.request_json(
            "PUT",
            f"/interactions/{safe_id}",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body={"code": code},
        )

    async def post_group_messages(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
        payload: T_JsonDict,
    ) -> PostGroupMessagesReturn:
        safe_gid = validate_qq_identifier(group_openid, "group_openid")
        data = await self._client.request_json(
            "POST",
            f"/v2/groups/{safe_gid}/messages",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )
        return PostGroupMessagesReturn.model_validate(data or {})

    async def delete_group_message(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
        message_id: str,
    ) -> None:
        safe_gid = validate_qq_identifier(group_openid, "group_openid")
        safe_mid = validate_qq_identifier(message_id, "message_id")
        await self._client.request_json(
            "DELETE",
            f"/v2/groups/{safe_gid}/messages/{safe_mid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def post_c2c_messages(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        openid: str,
        payload: T_JsonDict,
    ) -> PostC2CMessagesReturn:
        safe_uid = validate_qq_identifier(openid, "openid")
        data = await self._client.request_json(
            "POST",
            f"/v2/users/{safe_uid}/messages",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=payload,
        )
        return PostC2CMessagesReturn.model_validate(data or {})

    async def delete_c2c_message(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        openid: str,
        message_id: str,
    ) -> None:
        safe_uid = validate_qq_identifier(openid, "openid")
        safe_mid = validate_qq_identifier(message_id, "message_id")
        await self._client.request_json(
            "DELETE",
            f"/v2/users/{safe_uid}/messages/{safe_mid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )

    async def send_stream_chunk(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        target_id: str,
        is_c2c: bool,
        content: str,
        index: int,
        state: StreamState,
        stream_id: str | None = None,
        msg_id: str | None = None,
        msg_seq: int | None = None,
        use_markdown: bool = True,
        keyboard: T_JsonDict | None = None,
    ) -> PostGroupMessagesReturn | PostC2CMessagesReturn:
        stream_obj: T_JsonDict = {"state": int(state), "index": index}
        if stream_id:
            stream_obj["id"] = stream_id

        payload: T_JsonDict = {
            "msg_type": int(QQMsgType.MARKDOWN if use_markdown else QQMsgType.TEXT),
            "stream": stream_obj,
        }
        if use_markdown:
            payload["markdown"] = {"content": content}
        else:
            payload["content"] = content
        if keyboard is not None:
            payload["keyboard"] = keyboard
        if msg_id is not None:
            payload["msg_id"] = msg_id
        if msg_seq is not None:
            payload["msg_seq"] = msg_seq

        if is_c2c:
            return await self.post_c2c_messages(
                bot_config=bot_config,
                token_manager=token_manager,
                openid=target_id,
                payload=payload,
            )
        return await self.post_group_messages(
            bot_config=bot_config,
            token_manager=token_manager,
            group_openid=target_id,
            payload=payload,
        )


class MessageStream:
    """Async context manager for QQ v2 typewriter streaming replies."""

    def __init__(
        self,
        gateway: "Gateway",
        *,
        target_id: str,
        is_c2c: bool,
        msg_id: str | None = None,
        use_markdown: bool = True,
    ) -> None:
        self._gateway = gateway
        self._target_id = target_id
        self._is_c2c = is_c2c
        self._msg_id = msg_id
        self._use_markdown = use_markdown
        self.stream_id: str | None = None
        self._index: int = 0
        self._buffer: list[str] = []
        self._finished: bool = False

    async def __aenter__(self) -> Self:
        return self

    async def append(self, text: str) -> None:
        """Append incremental text and push a generating stream chunk."""
        if self._finished:
            return
        self._buffer.append(text)
        self._index += 1
        res = await self._gateway.send_stream_chunk(
            target_id=self._target_id,
            is_c2c=self._is_c2c,
            content="".join(self._buffer),
            index=self._index,
            state=StreamState.GENERATING,
            stream_id=self.stream_id,
            msg_id=self._msg_id,
            use_markdown=self._use_markdown,
        )
        if not self.stream_id and res.id:
            self.stream_id = res.id

    async def finish(
        self,
        final_text: str | None = None,
        *,
        keyboard: T_JsonDict | None = None,
    ) -> Any:
        """Send the final state=10 chunk to finalize the stream bubble."""
        if self._finished:
            return None
        self._finished = True
        content = final_text if final_text is not None else "".join(self._buffer)
        self._index += 1
        return await self._gateway.send_stream_chunk(
            target_id=self._target_id,
            is_c2c=self._is_c2c,
            content=content or " ",
            index=self._index,
            state=StreamState.FINISHED,
            stream_id=self.stream_id,
            msg_id=self._msg_id,
            use_markdown=self._use_markdown,
            keyboard=keyboard,
        )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if not self._finished and self._buffer:
            await self.finish()


__all__ = ["MessageStream", "MessagingService"]
