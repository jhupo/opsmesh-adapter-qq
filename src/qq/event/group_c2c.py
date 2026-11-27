"""QQ v2 C2C and Group message events."""

from typing import Any
from typing_extensions import override

from pydantic import Field

from .base import MessageEvent
from .models import Attachment, C2CAuthor, GroupAuthor, MessageReference


class C2CMessageCreateEvent(MessageEvent):
    """Inbound private C2C chat message (C2C_MESSAGE_CREATE)."""

    author: C2CAuthor = Field(default_factory=C2CAuthor)
    attachments: list[Attachment] = Field(default_factory=list)
    message_reference: MessageReference | None = None

    @override
    def get_event_name(self) -> str:
        return "message.c2c"

    @override
    def get_event_description(self) -> str:
        return (
            f"C2C message {self.id} from {self.get_user_id()}: "
            f"{self.message.extract_plain_text()!r}"
        )

    @override
    def get_user_id(self) -> str:
        return self.author.user_openid or self.author.id

    @override
    def get_session_id(self) -> str:
        return f"c2c_{self.get_user_id()}"

    @override
    def is_tome(self) -> bool:
        return True


class GroupMessageEvent(MessageEvent):
    """Base class for QQ v2 group message events."""

    group_openid: str = ""
    author: GroupAuthor = Field(default_factory=GroupAuthor)
    attachments: list[Attachment] = Field(default_factory=list)
    mentions: list[dict[str, Any]] = Field(default_factory=list)
    message_reference: MessageReference | None = None

    @override
    def get_user_id(self) -> str:
        return self.author.member_openid or self.author.id

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_openid}_{self.get_user_id()}"


class GroupAtMessageCreateEvent(GroupMessageEvent):
    """Inbound group @bot message (GROUP_AT_MESSAGE_CREATE)."""

    @override
    def get_event_name(self) -> str:
        return "message.group.at"

    @override
    def get_event_description(self) -> str:
        return (
            f"GroupAt message {self.id} in {self.group_openid} "
            f"from {self.get_user_id()}: {self.message.extract_plain_text()!r}"
        )

    @override
    def is_tome(self) -> bool:
        return True


class GroupMessageCreateEvent(GroupMessageEvent):
    """Inbound full group message (GROUP_MESSAGE_CREATE)."""

    to_me: bool = Field(default=False, exclude=True)

    @override
    def get_event_name(self) -> str:
        return "message.group"

    @override
    def get_event_description(self) -> str:
        return (
            f"Group message {self.id} in {self.group_openid} "
            f"from {self.get_user_id()}: {self.message.extract_plain_text()!r}"
        )

    @override
    def is_tome(self) -> bool:
        if self.to_me:
            return True
        return any(bool(m.get("is_you")) for m in self.mentions)


__all__ = [
    "C2CMessageCreateEvent",
    "GroupAtMessageCreateEvent",
    "GroupMessageCreateEvent",
    "GroupMessageEvent",
]
