"""Pydantic v2 data models for QQ Official Bot v1/v2 APIs and events."""

from datetime import datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class QQModel(BaseModel):
    """Base Pydantic v2 model allowing forward-compatible extra fields."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


# --- Common & Author Models ---


class User(QQModel):
    id: str = ""
    username: str = ""
    avatar: str = ""
    bot: bool = False
    union_openid: str | None = None
    union_user_account: str | None = None


class Attachment(QQModel):
    url: str = ""
    content_type: str = ""
    filename: str = ""
    size: int | None = None
    width: int | None = None
    height: int | None = None


class GroupAuthor(QQModel):
    id: str = ""
    member_openid: str = ""
    union_openid: str | None = None
    member_role: str = "member"


class C2CAuthor(QQModel):
    id: str = ""
    user_openid: str = ""
    union_openid: str | None = None


class GuildMember(QQModel):
    user: User | None = None
    nick: str = ""
    roles: list[str] = Field(default_factory=list)
    joined_at: str | None = None


class MessageReference(QQModel):
    message_id: str = ""
    ignore_get_message_error: bool = True


# --- Messaging & Media Return Models ---


class PostGroupMessagesReturn(QQModel):
    id: str = ""
    timestamp: str | int | None = None


class PostC2CMessagesReturn(QQModel):
    id: str = ""
    timestamp: str | int | None = None


class PostFilesReturn(QQModel):
    file_uuid: str = ""
    file_info: str = ""
    ttl: int = 0
    id: str | None = None


class UploadPartInfo(QQModel):
    index: int
    presigned_url: str


class UploadPrepareReturn(QQModel):
    upload_id: str
    block_size: int = 1024 * 1024
    parts: list[UploadPartInfo] = Field(default_factory=list)
    upload_config: dict[str, Any] = Field(default_factory=dict)


class ShardGatewayReturn(QQModel):
    url: str
    shards: int = 1
    session_start_limit: dict[str, Any] = Field(default_factory=dict)


# --- Official Group Admin v2 Models (11+ endpoints) ---


class GroupInfoReturn(QQModel):
    group_openid: str = ""
    group_name: str = ""
    member_count: int = 0
    max_member_count: int = 0
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class GroupBotStateReturn(QQModel):
    member_role: str = "member"
    allow_proactive_msg: bool = False
    recv_msg_setting: int | str | None = None


class GroupMemberInfo(QQModel):
    member_openid: str = ""
    username: str = ""
    member_role: str = "member"
    joined_at: str | int | None = None
    bot: bool = False


class GroupMembersReturn(QQModel):
    members: list[GroupMemberInfo] = Field(default_factory=list)
    next_cursor: str | None = None
    is_end: bool = True


class PostGroupMembersReturn(QQModel):
    members: list[GroupMemberInfo] = Field(default_factory=list)
    next_index: int | None = None


class MutedMemberInfo(QQModel):
    member_openid: str = ""
    mute_end_timestamp: str | int | None = None


class GroupRestrictChatSettingReturn(QQModel):
    all_muted: bool = False
    mute_all: bool = False
    muted_members: list[MutedMemberInfo] = Field(default_factory=list)


class SetMemberMuteState(QQModel):
    """Single member mute operation passed to set_group_members_mute."""

    member_openid: str
    op: Literal["add", "update", "del"] = "add"
    mute_end_timestamp: str | datetime | timedelta | None = None


class JoinRequestItem(QQModel):
    join_request_id: str = ""
    member_openid: str = ""
    username: str = ""
    apply_source: str = ""
    invited_by: str | None = None
    verify_info: str = ""
    risk_tips: str = ""
    status: str | int | None = None
    created_at: str | int | None = None


class JoinRequestListReturn(QQModel):
    join_requests: list[JoinRequestItem] = Field(default_factory=list)
    next_cursor: str | None = None
    is_end: bool = True


class BatchRemoveMembersReturn(QQModel):
    removed_member_openids: list[str] = Field(default_factory=list)
    failed_member_openids: list[str] = Field(default_factory=list)
    blacklist_failed_member_openids: list[str] = Field(default_factory=list)


class BlacklistMemberInfo(QQModel):
    member_openid: str = ""
    added_at: str | int | None = None


class GroupMemberBlacklistReturn(QQModel):
    members: list[BlacklistMemberInfo] = Field(default_factory=list)
    next_cursor: str | None = None
    is_end: bool = True


class MemberBlacklistOpReturn(QQModel):
    success_member_openids: list[str] = Field(default_factory=list)
    failed_member_openids: list[str] = Field(default_factory=list)


__all__ = [
    "Attachment",
    "BatchRemoveMembersReturn",
    "BlacklistMemberInfo",
    "C2CAuthor",
    "GroupAuthor",
    "GroupBotStateReturn",
    "GroupInfoReturn",
    "GroupMemberBlacklistReturn",
    "GroupMemberInfo",
    "GroupMembersReturn",
    "GroupRestrictChatSettingReturn",
    "GuildMember",
    "JoinRequestItem",
    "JoinRequestListReturn",
    "MemberBlacklistOpReturn",
    "MessageReference",
    "MutedMemberInfo",
    "PostC2CMessagesReturn",
    "PostFilesReturn",
    "PostGroupMembersReturn",
    "PostGroupMessagesReturn",
    "QQModel",
    "SetMemberMuteState",
    "ShardGatewayReturn",
    "UploadPartInfo",
    "UploadPrepareReturn",
    "User",
]
