"""QQ Guild v1 channel and DMS events."""

from typing_extensions import override

from pydantic import Field

from .base import MessageEvent, NoticeEvent
from .models import Attachment, GuildMember, MessageReference, User


class GuildMessageEvent(MessageEvent):
    """Base class for Guild v1 channel and DMS messages."""

    guild_id: str = ""
    channel_id: str = ""
    author: User = Field(default_factory=User)
    member: GuildMember | None = None
    mentions: list[User] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    message_reference: MessageReference | None = None

    @override
    def get_user_id(self) -> str:
        return self.author.id

    @override
    def get_session_id(self) -> str:
        return f"guild_{self.guild_id}_{self.channel_id}_{self.author.id}"


class AtMessageCreateEvent(GuildMessageEvent):
    """Public guild @bot channel message (AT_MESSAGE_CREATE)."""

    @override
    def get_event_name(self) -> str:
        return "message.guild.at"

    @override
    def get_event_description(self) -> str:
        return (
            f"GuildAt message {self.id} in {self.guild_id}/{self.channel_id} "
            f"from {self.author.id}: {self.message.extract_plain_text()!r}"
        )

    @override
    def is_tome(self) -> bool:
        return True


class MessageCreateEvent(GuildMessageEvent):
    """Private guild full channel message (MESSAGE_CREATE)."""

    to_me: bool = Field(default=False, exclude=True)

    @override
    def get_event_name(self) -> str:
        return "message.guild"

    @override
    def get_event_description(self) -> str:
        return (
            f"Guild message {self.id} in {self.guild_id}/{self.channel_id} "
            f"from {self.author.id}: {self.message.extract_plain_text()!r}"
        )

    @override
    def is_tome(self) -> bool:
        return self.to_me


class DirectMessageCreateEvent(GuildMessageEvent):
    """Guild direct message (DIRECT_MESSAGE_CREATE)."""

    @override
    def get_event_name(self) -> str:
        return "message.guild.direct"

    @override
    def get_event_description(self) -> str:
        return (
            f"DMS message {self.id} in {self.guild_id} "
            f"from {self.author.id}: {self.message.extract_plain_text()!r}"
        )

    @override
    def get_session_id(self) -> str:
        return f"dms_{self.guild_id}_{self.author.id}"

    @override
    def is_tome(self) -> bool:
        return True


class GuildNoticeEvent(NoticeEvent):
    """Generic Guild v1 notice event (guild/channel/member/reaction/audit/forum)."""

    guild_id: str = ""
    channel_id: str = ""
    user_id: str = ""

    @override
    def get_event_name(self) -> str:
        suffix = (self.raw_event_type or "unknown").lower()
        return f"notice.guild.{suffix}"

    @override
    def get_event_description(self) -> str:
        return f"GuildNotice {self.raw_event_type} guild={self.guild_id}"

    @override
    def get_user_id(self) -> str:
        return self.user_id

    @override
    def get_session_id(self) -> str:
        return f"guild_notice_{self.guild_id}_{self.channel_id}"


__all__ = [
    "AtMessageCreateEvent",
    "DirectMessageCreateEvent",
    "GuildMessageEvent",
    "GuildNoticeEvent",
    "MessageCreateEvent",
]
