"""QQ v2 group and C2C notice events (join requests, member changes, bot toggles)."""

from typing_extensions import override

from .base import NoticeEvent
from .models import VerifyInfo


class GroupNoticeEvent(NoticeEvent):
    """Base notice event scoped to a QQ group."""

    group_openid: str = ""
    timestamp: str | int = ""

    @override
    def get_session_id(self) -> str:
        return f"group_notice_{self.group_openid}"


class GroupJoinRequestEvent(GroupNoticeEvent):
    """User applied to join a group (GROUP_JOIN_REQUEST)."""

    join_request_id: str = ""
    member_openid: str = ""
    username: str = ""
    apply_source: str = ""
    invited_by: str | None = None
    verify_info: VerifyInfo | str | None = None
    risk_tips: str | None = None
    auto_approved: bool = False

    @override
    def get_event_name(self) -> str:
        return "notice.group_join_request"

    @override
    def get_event_description(self) -> str:
        return (
            f"GroupJoinRequest {self.join_request_id} in {self.group_openid} "
            f"from {self.member_openid}"
        )

    @override
    def get_user_id(self) -> str:
        return self.member_openid


class GroupMemberAddEvent(GroupNoticeEvent):
    """Member joined a group (GROUP_MEMBER_ADD)."""

    member_openid: str = ""

    @override
    def get_event_name(self) -> str:
        return "notice.group_member_add"

    @override
    def get_event_description(self) -> str:
        return f"GroupMemberAdd {self.member_openid} in {self.group_openid}"

    @override
    def get_user_id(self) -> str:
        return self.member_openid


class GroupMemberRemoveEvent(GroupNoticeEvent):
    """Member left or was removed from a group (GROUP_MEMBER_REMOVE)."""

    member_openid: str = ""

    @override
    def get_event_name(self) -> str:
        return "notice.group_member_remove"

    @override
    def get_event_description(self) -> str:
        return f"GroupMemberRemove {self.member_openid} in {self.group_openid}"

    @override
    def get_user_id(self) -> str:
        return self.member_openid


class GroupAddRobotEvent(GroupNoticeEvent):
    """Bot was added to a group (GROUP_ADD_ROBOT)."""

    op_member_openid: str = ""

    @override
    def get_event_name(self) -> str:
        return "notice.group_add_robot"

    @override
    def get_event_description(self) -> str:
        return f"GroupAddRobot in {self.group_openid} by {self.op_member_openid}"

    @override
    def get_user_id(self) -> str:
        return self.op_member_openid


class GroupDelRobotEvent(GroupNoticeEvent):
    """Bot was removed from a group (GROUP_DEL_ROBOT)."""

    op_member_openid: str = ""

    @override
    def get_event_name(self) -> str:
        return "notice.group_del_robot"

    @override
    def get_event_description(self) -> str:
        return f"GroupDelRobot in {self.group_openid} by {self.op_member_openid}"

    @override
    def get_user_id(self) -> str:
        return self.op_member_openid


class GroupMsgReceiveEvent(GroupNoticeEvent):
    """Group enabled proactive messages from bot (GROUP_MSG_RECEIVE)."""

    op_member_openid: str = ""

    @override
    def get_event_name(self) -> str:
        return "notice.group_msg_receive"

    @override
    def get_event_description(self) -> str:
        return f"GroupMsgReceive in {self.group_openid}"

    @override
    def get_user_id(self) -> str:
        return self.op_member_openid


class GroupMsgRejectEvent(GroupNoticeEvent):
    """Group disabled proactive messages from bot (GROUP_MSG_REJECT)."""

    op_member_openid: str = ""

    @override
    def get_event_name(self) -> str:
        return "notice.group_msg_reject"

    @override
    def get_event_description(self) -> str:
        return f"GroupMsgReject in {self.group_openid}"

    @override
    def get_user_id(self) -> str:
        return self.op_member_openid


class FriendNoticeEvent(NoticeEvent):
    """Base C2C friend / proactive toggle notice."""

    openid: str = ""
    timestamp: str | int = ""

    @override
    def get_user_id(self) -> str:
        return self.openid

    @override
    def get_session_id(self) -> str:
        return f"c2c_notice_{self.openid}"


class FriendAddEvent(FriendNoticeEvent):
    """User added bot as friend (FRIEND_ADD)."""

    @override
    def get_event_name(self) -> str:
        return "notice.friend_add"

    @override
    def get_event_description(self) -> str:
        return f"FriendAdd {self.openid}"


class FriendDelEvent(FriendNoticeEvent):
    """User removed bot as friend (FRIEND_DEL)."""

    @override
    def get_event_name(self) -> str:
        return "notice.friend_del"

    @override
    def get_event_description(self) -> str:
        return f"FriendDel {self.openid}"


class C2CMsgReceiveEvent(FriendNoticeEvent):
    """User enabled proactive C2C messages (C2C_MSG_RECEIVE)."""

    @override
    def get_event_name(self) -> str:
        return "notice.c2c_msg_receive"

    @override
    def get_event_description(self) -> str:
        return f"C2CMsgReceive {self.openid}"


class C2CMsgRejectEvent(FriendNoticeEvent):
    """User disabled proactive C2C messages (C2C_MSG_REJECT)."""

    @override
    def get_event_name(self) -> str:
        return "notice.c2c_msg_reject"

    @override
    def get_event_description(self) -> str:
        return f"C2CMsgReject {self.openid}"


__all__ = [
    "C2CMsgReceiveEvent",
    "C2CMsgRejectEvent",
    "FriendAddEvent",
    "FriendDelEvent",
    "FriendNoticeEvent",
    "GroupAddRobotEvent",
    "GroupDelRobotEvent",
    "GroupJoinRequestEvent",
    "GroupMemberAddEvent",
    "GroupMemberRemoveEvent",
    "GroupMsgReceiveEvent",
    "GroupMsgRejectEvent",
    "GroupNoticeEvent",
]
