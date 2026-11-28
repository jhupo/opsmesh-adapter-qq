"""Pydantic v2 data models for QQ Official Bot v1/v2 APIs and events."""

import builtins
from datetime import datetime, time, timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from qq.utils import format_iso8601_utc


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
    timestamp: datetime | str | int | None = None


class PostC2CMessagesReturn(QQModel):
    id: str = ""
    timestamp: datetime | str | int | None = None


class PostFilesReturn(QQModel):
    file_uuid: str = ""
    file_info: str = ""
    ttl: int = 0
    id: str | None = None


class UploadPartInfo(QQModel):
    index: int
    presigned_url: str


class UploadConfig(QQModel):
    concurrency: int = 4
    retry_timeout: int = 30
    retry_delay: int = 5


class UploadPrepareReturn(QQModel):
    upload_id: str
    block_size: int = 1024 * 1024
    parts: list[UploadPartInfo] = Field(default_factory=list)
    upload_config: UploadConfig = Field(default_factory=UploadConfig)


class ShardGatewayReturn(QQModel):
    url: str
    shards: int = 1
    session_start_limit: dict[str, Any] = Field(default_factory=dict)


# --- Official Group Admin v2 Models (100% aligned with Tencent Open Platform v2) ---


class GroupInfoReturn(QQModel):
    group_openid: str = ""
    group_name: str = ""
    group_finger_memo: str = ""
    group_class_text: str = ""
    group_tags: list[str] = Field(default_factory=list)
    group_member_num: int = 0


class GroupBotStateReturn(QQModel):
    member_openid: str = ""
    joined_at: datetime | str | None = None
    allow_proactive_msg: bool = False
    recv_msg_setting: str = "only_mention"
    member_role: str = "member"


class GroupMember(QQModel):
    member_openid: str = ""
    join_timestamp: datetime | str | None = None


class PostGroupMembersReturn(QQModel):
    members: list[GroupMember] = Field(default_factory=list)
    next_index: int | None = None


class GroupMemberInfo(QQModel):
    member_openid: str = ""
    username: str | None = None
    member_role: str = "member"
    bot: bool = False
    joined_at: datetime | str | None = None
    union_openid: str | None = None


class GroupMembersReturn(QQModel):
    members: list[GroupMemberInfo] = Field(default_factory=list)
    next_cursor: str | None = None


class MemberMuteState(QQModel):
    member_openid: str = ""
    mute_expire_at: datetime | str | None = None
    username: str = ""
    union_openid: str | None = None


class MuteScheduleRule(QQModel):
    task_id: str = ""
    start_at: datetime | str | None = None
    end_at: datetime | str | None = None
    enabled: bool = False


class MuteRecurringRule(QQModel):
    task_id: str = ""
    weekdays: list[int] = Field(default_factory=list)
    start_time: time | str | None = None
    end_time: time | str | None = None
    enabled: bool = False


class GlobalMuteRule(QQModel):
    mode: str = "none"
    schedule_rules: list[MuteScheduleRule] = Field(default_factory=list)
    recurring_rules: list[MuteRecurringRule] = Field(default_factory=list)


class GroupRestrictChatSettingReturn(QQModel):
    global_rule: GlobalMuteRule = Field(default_factory=GlobalMuteRule)
    members: list[MemberMuteState] = Field(default_factory=list)


class SetMemberMuteState(QQModel):
    """Single member mute operation passed to set_group_members_mute."""

    member_openid: str
    op: Literal["add", "update", "del"] = "add"
    mute_expire_at: str | datetime | timedelta | None = None

    @field_validator("mute_expire_at", mode="before")
    @classmethod
    def _normalize_expire(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, (datetime, timedelta)):
            return format_iso8601_utc(value)
        return str(value)


class ReviewQA(QQModel):
    question: str = ""
    answer: str = ""


class VerifyInfo(QQModel):
    method: str = ""
    verify_message: str | None = None
    review_qa_list: list[ReviewQA] | None = None


class JoinRequest(QQModel):
    join_request_id: str = ""
    risk_tips: str | None = None
    union_openid: str | None = None
    member_openid: str = ""
    username: str = ""
    apply_at: datetime | str | None = None
    apply_source: str = "self_apply"
    invited_by: str | None = None
    bot: bool = False
    verify_info: VerifyInfo | None = None


class JoinRequestListReturn(QQModel):
    list: builtins.list[JoinRequest] = Field(default_factory=builtins.list)
    next_cursor: str = ""


class BatchRemoveMembersReturn(QQModel):
    remove_members_result: str | None = None
    add_to_member_blacklist_fail_openids: list[str] = Field(default_factory=list)


class BlacklistUser(QQModel):
    union_openid: str | None = None
    member_openid: str = ""
    username: str | None = None
    banned_at: datetime | str | None = None
    bot: bool = False


class GroupMemberBlacklistReturn(QQModel):
    users: list[BlacklistUser] = Field(default_factory=list)
    next_cursor: str | None = None


class MemberBlacklistOpReturn(QQModel):
    fail_openids: list[str] = Field(default_factory=list)


__all__ = [
    "Attachment",
    "BatchRemoveMembersReturn",
    "BlacklistUser",
    "C2CAuthor",
    "GlobalMuteRule",
    "GroupAuthor",
    "GroupBotStateReturn",
    "GroupInfoReturn",
    "GroupMember",
    "GroupMemberBlacklistReturn",
    "GroupMemberInfo",
    "GroupMembersReturn",
    "GroupRestrictChatSettingReturn",
    "GuildMember",
    "JoinRequest",
    "JoinRequestListReturn",
    "MemberBlacklistOpReturn",
    "MemberMuteState",
    "MessageReference",
    "MuteRecurringRule",
    "MuteScheduleRule",
    "PostC2CMessagesReturn",
    "PostFilesReturn",
    "PostGroupMembersReturn",
    "PostGroupMessagesReturn",
    "QQModel",
    "ReviewQA",
    "SetMemberMuteState",
    "ShardGatewayReturn",
    "UploadConfig",
    "UploadPartInfo",
    "UploadPrepareReturn",
    "User",
    "VerifyInfo",
]
