"""QQ Official Bot Gateway facade: send routing, passive msg_seq, and typed APIs."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
from typing_extensions import override

from opsmesh.adapters import Event as BaseEvent
from opsmesh.adapters import Gateway as BaseGateway
from opsmesh.adapters import Message as BaseMessage
from opsmesh.adapters import MessageSegment as BaseMessageSegment
from opsmesh.adapters import MessageTemplate

from qq.api.messaging import MessageStream
from qq.config import BotConfig
from qq.event import (
    BatchRemoveMembersReturn,
    C2CMessageCreateEvent,
    DirectMessageCreateEvent,
    GroupBotStateReturn,
    GroupInfoReturn,
    GroupMemberBlacklistReturn,
    GroupMemberInfo,
    GroupMembersReturn,
    GroupMessageEvent,
    GroupNoticeEvent,
    GroupRestrictChatSettingReturn,
    GuildMessageEvent,
    InteractionCreateEvent,
    JoinRequestListReturn,
    MemberBlacklistOpReturn,
    PostC2CMessagesReturn,
    PostFilesReturn,
    PostGroupMembersReturn,
    PostGroupMessagesReturn,
    SetMemberMuteState,
    User,
)
from qq.exception import MediaError, QQActionFailed
from qq.message import (
    Message,
    MessageSegment,
    V2SendUnit,
    plan_v2_units,
    serialize_guild_message,
)
from qq.typing import MediaFileType, QQAction, StreamState, T_JsonDict
from qq.utils import PassiveReplyTracker

if TYPE_CHECKING:
    from qq.adapter import Adapter


def _coerce_message(
    message: str | BaseMessage | BaseMessageSegment | MessageTemplate,
) -> Message:
    if isinstance(message, Message):
        return message
    if isinstance(message, MessageSegment):
        return Message(message)
    if isinstance(message, str):
        return Message(message)
    return Message(str(message))


class Gateway(BaseGateway):
    """QQ Official Bot gateway instance managed by qq.Adapter."""

    adapter: "Adapter"

    def __init__(self, adapter: "Adapter", bot_config: BotConfig) -> None:
        super().__init__(adapter, bot_config.gateway_id)
        self.bot_config: BotConfig = bot_config
        self.self_info: User | None = None
        self.passive_tracker: PassiveReplyTracker = PassiveReplyTracker()

    @property
    def app_id(self) -> str:
        return self.bot_config.app_id

    async def get_access_token(self, *, force_refresh: bool = False) -> str:
        return await self.invoke(QQAction.GET_ACCESS_TOKEN, force_refresh=force_refresh)

    async def me(self) -> User:
        return await self.invoke(QQAction.ME)

    async def put_interaction(self, interaction_id: str, *, code: int = 0) -> None:
        await self.invoke(
            QQAction.PUT_INTERACTION, interaction_id=interaction_id, code=code
        )

    # --- Unified Event Reply (OpsMesh Gateway.send) ---

    @override
    async def send(
        self,
        event: BaseEvent,
        message: str | BaseMessage | BaseMessageSegment | MessageTemplate,
        **kwargs: Any,
    ) -> Any:
        msg = _coerce_message(message)
        if not msg:
            return None

        if isinstance(event, GroupMessageEvent):
            return await self._send_v2_units(
                target_id=event.group_openid,
                is_c2c=False,
                message=msg,
                msg_id=event.id or None,
                event_id=event.event_id,
            )
        if isinstance(event, C2CMessageCreateEvent):
            return await self._send_v2_units(
                target_id=event.get_user_id(),
                is_c2c=True,
                message=msg,
                msg_id=event.id or None,
                event_id=event.event_id,
            )
        if isinstance(event, GroupNoticeEvent):
            return await self._send_v2_units(
                target_id=event.group_openid,
                is_c2c=False,
                message=msg,
                event_id=event.event_id,
            )
        if isinstance(event, DirectMessageCreateEvent):
            payload = serialize_guild_message(msg)
            return await self.invoke(
                QQAction.POST_DMS_MESSAGES,
                guild_id=event.guild_id,
                payload=payload.to_body(
                    msg_id=event.id or None, event_id=event.event_id
                ),
                file_image=payload.file_image,
            )
        if isinstance(event, GuildMessageEvent):
            payload = serialize_guild_message(msg)
            return await self.invoke(
                QQAction.POST_MESSAGES,
                channel_id=event.channel_id,
                payload=payload.to_body(
                    msg_id=event.id or None, event_id=event.event_id
                ),
                file_image=payload.file_image,
            )
        if isinstance(event, InteractionCreateEvent):
            if event.group_openid:
                return await self._send_v2_units(
                    target_id=event.group_openid,
                    is_c2c=False,
                    message=msg,
                    event_id=event.id or event.event_id,
                )
            if event.user_openid:
                return await self._send_v2_units(
                    target_id=event.user_openid,
                    is_c2c=True,
                    message=msg,
                    event_id=event.id or event.event_id,
                )

        raise QQActionFailed(
            f"Cannot determine QQ reply target for event {type(event).__name__}."
        )

    async def send_group_message(
        self,
        group_openid: str,
        message: str | Message | MessageSegment,
        *,
        msg_id: str | None = None,
        event_id: str | None = None,
    ) -> Any:
        return await self._send_v2_units(
            target_id=group_openid,
            is_c2c=False,
            message=_coerce_message(message),
            msg_id=msg_id,
            event_id=event_id,
        )

    async def send_c2c_message(
        self,
        openid: str,
        message: str | Message | MessageSegment,
        *,
        msg_id: str | None = None,
        event_id: str | None = None,
    ) -> Any:
        return await self._send_v2_units(
            target_id=openid,
            is_c2c=True,
            message=_coerce_message(message),
            msg_id=msg_id,
            event_id=event_id,
        )

    async def _send_v2_units(
        self,
        *,
        target_id: str,
        is_c2c: bool,
        message: Message,
        msg_id: str | None = None,
        event_id: str | None = None,
    ) -> Any:
        units = plan_v2_units(message, auto_markdown=self.bot_config.auto_markdown)
        results: list[Any] = []
        for unit in units:
            file_info = await self._resolve_unit_file_info(
                target_id=target_id, is_c2c=is_c2c, unit=unit
            )
            seq: int | None = None
            effective_msg_id = msg_id
            if effective_msg_id:
                seq = await self.passive_tracker.allocate_seq(
                    effective_msg_id, is_c2c=is_c2c
                )
                if seq is None:
                    effective_msg_id = None

            payload = unit.to_payload(
                file_info=file_info,
                msg_id=effective_msg_id,
                event_id=event_id if effective_msg_id is None else None,
                msg_seq=seq,
            )
            if is_c2c:
                res = await self.invoke(
                    QQAction.POST_C2C_MESSAGES, openid=target_id, payload=payload
                )
            else:
                res = await self.invoke(
                    QQAction.POST_GROUP_MESSAGES,
                    group_openid=target_id,
                    payload=payload,
                )
            results.append(res)
        return results[0] if len(results) == 1 else results

    async def _resolve_unit_file_info(
        self,
        *,
        target_id: str,
        is_c2c: bool,
        unit: V2SendUnit,
    ) -> str | None:
        seg = unit.media_segment
        if seg is None or unit.media_file_type is None:
            return None
        if seg.data.get("file_info"):
            return str(seg.data["file_info"])
        if seg.data.get("url"):
            action = QQAction.POST_C2C_FILES if is_c2c else QQAction.POST_GROUP_FILES
            key = "openid" if is_c2c else "group_openid"
            uploaded: PostFilesReturn = await self.invoke(
                action,
                **{
                    key: target_id,
                    "file_type": unit.media_file_type,
                    "url": str(seg.data["url"]),
                },
            )
            return uploaded.file_info
        raw_bytes = seg.data.get("content")
        path = seg.data.get("path")
        if raw_bytes is None and path is None:
            raise MediaError(
                f"Outbound {seg.type!r} segment needs file_info, url, path, or content."
            )
        uploaded = await self.adapter._media.upload_bytes_or_path(
            bot_config=self.bot_config,
            token_manager=self.adapter._token_managers[self.id],
            target_id=target_id,
            is_c2c=is_c2c,
            file_type=unit.media_file_type,
            raw_bytes=bytes(raw_bytes)
            if isinstance(raw_bytes, (bytes, bytearray))
            else None,
            path=Path(path) if path is not None else None,
            filename=str(seg.data.get("filename") or "file.bin"),
        )
        return uploaded.file_info

    # --- Streaming Messages (MessageStream) ---

    async def send_stream_chunk(
        self,
        *,
        target_id: str,
        is_c2c: bool,
        content: str,
        index: int,
        state: StreamState,
        stream_id: str | None = None,
        msg_id: str | None = None,
        use_markdown: bool = True,
        keyboard: T_JsonDict | None = None,
    ) -> PostGroupMessagesReturn | PostC2CMessagesReturn:
        seq: int | None = None
        effective_msg_id = msg_id
        if effective_msg_id:
            seq = await self.passive_tracker.allocate_seq(
                effective_msg_id, is_c2c=is_c2c
            )
            if seq is None:
                effective_msg_id = None
        action = QQAction.SEND_C2C_STREAM if is_c2c else QQAction.SEND_GROUP_STREAM
        return await self.invoke(
            action,
            target_id=target_id,
            is_c2c=is_c2c,
            content=content,
            index=index,
            state=state,
            stream_id=stream_id,
            msg_id=effective_msg_id,
            msg_seq=seq,
            use_markdown=use_markdown,
            keyboard=keyboard,
        )

    def message_stream(
        self,
        event: GroupMessageEvent | C2CMessageCreateEvent,
        *,
        use_markdown: bool = True,
    ) -> MessageStream:
        """Create a MessageStream async context manager for a Group or C2C event."""
        if isinstance(event, C2CMessageCreateEvent):
            return MessageStream(
                self,
                target_id=event.get_user_id(),
                is_c2c=True,
                msg_id=event.id or None,
                use_markdown=use_markdown,
            )
        return MessageStream(
            self,
            target_id=event.group_openid,
            is_c2c=False,
            msg_id=event.id or None,
            use_markdown=use_markdown,
        )

    # --- Recall & Media Helpers ---

    async def delete_group_message(self, group_openid: str, message_id: str) -> None:
        await self.invoke(
            QQAction.DELETE_GROUP_MESSAGE,
            group_openid=group_openid,
            message_id=message_id,
        )

    async def delete_c2c_message(self, openid: str, message_id: str) -> None:
        await self.invoke(
            QQAction.DELETE_C2C_MESSAGE,
            openid=openid,
            message_id=message_id,
        )

    async def post_group_files(
        self,
        group_openid: str,
        file_type: MediaFileType | int,
        *,
        url: str | None = None,
        file_data: bytes | str | None = None,
        srv_send_msg: bool = False,
    ) -> PostFilesReturn:
        return await self.invoke(
            QQAction.POST_GROUP_FILES,
            group_openid=group_openid,
            file_type=file_type,
            url=url,
            file_data=file_data,
            srv_send_msg=srv_send_msg,
        )

    async def post_c2c_files(
        self,
        openid: str,
        file_type: MediaFileType | int,
        *,
        url: str | None = None,
        file_data: bytes | str | None = None,
        srv_send_msg: bool = False,
    ) -> PostFilesReturn:
        return await self.invoke(
            QQAction.POST_C2C_FILES,
            openid=openid,
            file_type=file_type,
            url=url,
            file_data=file_data,
            srv_send_msg=srv_send_msg,
        )

    async def download_attachment(
        self, url: str, *, max_bytes: int | None = None
    ) -> bytes:
        return await self.invoke(
            QQAction.DOWNLOAD_ATTACHMENT, url=url, max_bytes=max_bytes
        )

    # --- Official Group Admin v2 Facade (Full 11 endpoints) ---

    async def get_group_info(self, group_openid: str) -> GroupInfoReturn:
        return await self.invoke(QQAction.GET_GROUP_INFO, group_openid=group_openid)

    async def get_group_bot_state(self, group_openid: str) -> GroupBotStateReturn:
        return await self.invoke(
            QQAction.GET_GROUP_BOT_STATE, group_openid=group_openid
        )

    async def get_group_members(
        self,
        group_openid: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> GroupMembersReturn:
        return await self.invoke(
            QQAction.GET_GROUP_MEMBERS,
            group_openid=group_openid,
            cursor=cursor,
            limit=limit,
        )

    async def post_group_members(
        self,
        group_openid: str,
        *,
        limit: int | None = None,
        start_index: int | None = None,
    ) -> PostGroupMembersReturn:
        return await self.invoke(
            QQAction.POST_GROUP_MEMBERS,
            group_openid=group_openid,
            limit=limit,
            start_index=start_index,
        )

    async def get_group_member(
        self, group_openid: str, member_openid: str
    ) -> GroupMemberInfo:
        return await self.invoke(
            QQAction.GET_GROUP_MEMBER,
            group_openid=group_openid,
            member_openid=member_openid,
        )

    async def get_group_mute_setting(
        self, group_openid: str
    ) -> GroupRestrictChatSettingReturn:
        return await self.invoke(
            QQAction.GET_GROUP_MUTE_SETTING, group_openid=group_openid
        )

    async def set_group_members_mute(
        self,
        group_openid: str,
        members: list[SetMemberMuteState],
    ) -> None:
        await self.invoke(
            QQAction.SET_GROUP_MEMBERS_MUTE,
            group_openid=group_openid,
            members=members,
        )

    async def get_group_join_request_list(
        self,
        group_openid: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> JoinRequestListReturn:
        return await self.invoke(
            QQAction.GET_GROUP_JOIN_REQUEST_LIST,
            group_openid=group_openid,
            cursor=cursor,
            limit=limit,
        )

    async def approval_join_request(
        self,
        group_openid: str,
        member_openid: str,
        *,
        op: Literal["approve", "decline"],
        join_request_id: str | None = None,
        reject_reason: str | None = None,
        add_to_member_blacklist: bool | None = None,
    ) -> None:
        await self.invoke(
            QQAction.APPROVAL_JOIN_REQUEST,
            group_openid=group_openid,
            member_openid=member_openid,
            op=op,
            join_request_id=join_request_id,
            reject_reason=reject_reason,
            add_to_member_blacklist=add_to_member_blacklist,
        )

    async def batch_remove_group_members(
        self,
        group_openid: str,
        member_openids: list[str],
        *,
        add_to_member_blacklist: bool | None = None,
    ) -> BatchRemoveMembersReturn:
        return await self.invoke(
            QQAction.BATCH_REMOVE_GROUP_MEMBERS,
            group_openid=group_openid,
            member_openids=member_openids,
            add_to_member_blacklist=add_to_member_blacklist,
        )

    async def get_group_member_blacklist(
        self,
        group_openid: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> GroupMemberBlacklistReturn:
        return await self.invoke(
            QQAction.GET_GROUP_MEMBER_BLACKLIST,
            group_openid=group_openid,
            cursor=cursor,
            limit=limit,
        )

    async def post_group_member_blacklist(
        self,
        group_openid: str,
        *,
        op: Literal["add", "del"],
        member_openids: list[str],
    ) -> MemberBlacklistOpReturn:
        return await self.invoke(
            QQAction.POST_GROUP_MEMBER_BLACKLIST,
            group_openid=group_openid,
            op=op,
            member_openids=member_openids,
        )


__all__ = ["Gateway"]
