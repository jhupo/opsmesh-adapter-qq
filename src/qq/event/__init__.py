"""Event parser registry and unified exports for qq.event."""

from typing import Any

from qq.message import parse_inbound_message
from qq.typing import T_JsonDict

from .base import (
    MessageEvent,
    MetaEvent,
    NoticeEvent,
    QQEvent,
    ReadyEvent,
    ResumedEvent,
)
from .group_c2c import (
    C2CMessageCreateEvent,
    GroupAtMessageCreateEvent,
    GroupMessageCreateEvent,
    GroupMessageEvent,
)
from .group_notice import (
    C2CMsgReceiveEvent,
    C2CMsgRejectEvent,
    FriendAddEvent,
    FriendDelEvent,
    FriendNoticeEvent,
    GroupAddRobotEvent,
    GroupDelRobotEvent,
    GroupJoinRequestEvent,
    GroupMemberAddEvent,
    GroupMemberRemoveEvent,
    GroupMsgReceiveEvent,
    GroupMsgRejectEvent,
    GroupNoticeEvent,
)
from .guild import (
    AtMessageCreateEvent,
    DirectMessageCreateEvent,
    GuildMessageEvent,
    GuildNoticeEvent,
    MessageCreateEvent,
)
from .interaction import InteractionCreateEvent, InteractionData
from .models import (
    Attachment,
    BatchRemoveMembersReturn,
    BlacklistUser,
    C2CAuthor,
    GlobalMuteRule,
    GroupAuthor,
    GroupBotStateReturn,
    GroupInfoReturn,
    GroupMember,
    GroupMemberBlacklistReturn,
    GroupMemberInfo,
    GroupMembersReturn,
    GroupRestrictChatSettingReturn,
    GuildMember,
    JoinRequest,
    JoinRequestListReturn,
    MemberBlacklistOpReturn,
    MemberMuteState,
    MessageReference,
    MuteRecurringRule,
    MuteScheduleRule,
    PostC2CMessagesReturn,
    PostFilesReturn,
    PostGroupMembersReturn,
    PostGroupMessagesReturn,
    QQModel,
    ReviewQA,
    SetMemberMuteState,
    ShardGatewayReturn,
    UploadConfig,
    UploadPartInfo,
    UploadPrepareReturn,
    User,
    VerifyInfo,
)

_EVENT_CLASS_MAP: dict[str, type[QQEvent]] = {
    "READY": ReadyEvent,
    "RESUMED": ResumedEvent,
    "C2C_MESSAGE_CREATE": C2CMessageCreateEvent,
    "GROUP_AT_MESSAGE_CREATE": GroupAtMessageCreateEvent,
    "GROUP_MESSAGE_CREATE": GroupMessageCreateEvent,
    "GROUP_JOIN_REQUEST": GroupJoinRequestEvent,
    "GROUP_MEMBER_ADD": GroupMemberAddEvent,
    "GROUP_MEMBER_REMOVE": GroupMemberRemoveEvent,
    "GROUP_ADD_ROBOT": GroupAddRobotEvent,
    "GROUP_DEL_ROBOT": GroupDelRobotEvent,
    "GROUP_MSG_RECEIVE": GroupMsgReceiveEvent,
    "GROUP_MSG_REJECT": GroupMsgRejectEvent,
    "FRIEND_ADD": FriendAddEvent,
    "FRIEND_DEL": FriendDelEvent,
    "C2C_MSG_RECEIVE": C2CMsgReceiveEvent,
    "C2C_MSG_REJECT": C2CMsgRejectEvent,
    "AT_MESSAGE_CREATE": AtMessageCreateEvent,
    "MESSAGE_CREATE": MessageCreateEvent,
    "DIRECT_MESSAGE_CREATE": DirectMessageCreateEvent,
    "INTERACTION_CREATE": InteractionCreateEvent,
}


def parse_event(
    event_type: str,
    data: T_JsonDict | Any,
    *,
    event_id: str | None = None,
    bot_user_id: str | None = None,
) -> QQEvent:
    """Parse a raw QQ dispatch payload into a typed QQEvent subclass."""
    payload: T_JsonDict = dict(data) if isinstance(data, dict) else {}
    if event_id and "event_id" not in payload:
        payload["event_id"] = event_id

    event_cls = _EVENT_CLASS_MAP.get(event_type, GuildNoticeEvent)
    event = event_cls.model_validate(payload)
    event.raw_event_type = event_type
    event.raw_payload = payload

    if isinstance(event, MessageEvent):
        raw_attachments = payload.get("attachments")
        attachments = raw_attachments if isinstance(raw_attachments, list) else None
        strip_id = (
            bot_user_id
            if isinstance(
                event,
                (GroupAtMessageCreateEvent, AtMessageCreateEvent, MessageCreateEvent),
            )
            else None
        )
        event.message = parse_inbound_message(
            event.content,
            attachments=attachments,
            strip_leading_bot_id=strip_id,
        )
        if isinstance(event, MessageCreateEvent) and bot_user_id:
            event.to_me = any(m.id == bot_user_id for m in event.mentions)

    return event


__all__ = [
    "AtMessageCreateEvent",
    "Attachment",
    "BatchRemoveMembersReturn",
    "BlacklistUser",
    "C2CAuthor",
    "C2CMessageCreateEvent",
    "C2CMsgReceiveEvent",
    "C2CMsgRejectEvent",
    "DirectMessageCreateEvent",
    "FriendAddEvent",
    "FriendDelEvent",
    "FriendNoticeEvent",
    "GlobalMuteRule",
    "GroupAddRobotEvent",
    "GroupAtMessageCreateEvent",
    "GroupAuthor",
    "GroupBotStateReturn",
    "GroupDelRobotEvent",
    "GroupInfoReturn",
    "GroupJoinRequestEvent",
    "GroupMember",
    "GroupMemberAddEvent",
    "GroupMemberBlacklistReturn",
    "GroupMemberInfo",
    "GroupMemberRemoveEvent",
    "GroupMembersReturn",
    "GroupMessageCreateEvent",
    "GroupMessageEvent",
    "GroupMsgReceiveEvent",
    "GroupMsgRejectEvent",
    "GroupNoticeEvent",
    "GroupRestrictChatSettingReturn",
    "GuildMember",
    "GuildMessageEvent",
    "GuildNoticeEvent",
    "InteractionCreateEvent",
    "InteractionData",
    "JoinRequest",
    "JoinRequestListReturn",
    "MemberBlacklistOpReturn",
    "MemberMuteState",
    "MessageCreateEvent",
    "MessageEvent",
    "MessageReference",
    "MetaEvent",
    "MuteRecurringRule",
    "MuteScheduleRule",
    "NoticeEvent",
    "PostC2CMessagesReturn",
    "PostFilesReturn",
    "PostGroupMembersReturn",
    "PostGroupMessagesReturn",
    "QQEvent",
    "QQModel",
    "ReadyEvent",
    "ResumedEvent",
    "ReviewQA",
    "SetMemberMuteState",
    "ShardGatewayReturn",
    "UploadConfig",
    "UploadPartInfo",
    "UploadPrepareReturn",
    "User",
    "VerifyInfo",
    "parse_event",
]
