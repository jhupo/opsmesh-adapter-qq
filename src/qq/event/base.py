"""Base QQ Event classes inheriting opsmesh.adapters.Event."""

from typing_extensions import override

from opsmesh.adapters import Event as BaseEvent
from pydantic import ConfigDict, Field

from qq.exception import NoLogException
from qq.message import Message
from qq.typing import ADAPTER_NAME, T_JsonDict

from .models import User


class QQEvent(BaseEvent):
    """Abstract base class for all QQ Official Bot events."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    event_id: str | None = None
    raw_event_type: str = Field(default="", exclude=True)
    raw_payload: T_JsonDict = Field(default_factory=dict, exclude=True)


class MetaEvent(QQEvent):
    """Gateway lifecycle meta events (READY / RESUMED / DISCONNECTED)."""

    @override
    def get_type(self) -> str:
        return "meta_event"

    @override
    def get_user_id(self) -> str:
        raise ValueError(f"{self.__class__.__name__} has no user_id.")

    @override
    def get_session_id(self) -> str:
        return f"meta_{self.get_event_name()}"

    @override
    def get_message(self) -> Message:
        raise ValueError(f"{self.__class__.__name__} has no message.")

    @override
    def is_tome(self) -> bool:
        return False


class ReadyEvent(MetaEvent):
    """Emitted when a WebSocket shard finishes IDENTIFY."""

    version: int = 1
    session_id: str = ""
    user: User = Field(default_factory=User)
    shard: list[int] = Field(default_factory=list)

    @override
    def get_event_name(self) -> str:
        return "meta_event.ready"

    @override
    def get_event_description(self) -> str:
        return f"READY session_id={self.session_id} user={self.user.username}"


class ResumedEvent(MetaEvent):
    """Emitted when a WebSocket shard finishes OP_RESUME."""

    session_id: str = ""

    @override
    def get_event_name(self) -> str:
        return "meta_event.resumed"

    @override
    def get_event_description(self) -> str:
        return f"RESUMED session_id={self.session_id}"

    @override
    def get_log_string(self) -> str:
        raise NoLogException(ADAPTER_NAME)


class MessageEvent(QQEvent):
    """Base class for all inbound QQ message events."""

    id: str = ""
    content: str = ""
    timestamp: str | int = ""
    message: Message = Field(default_factory=Message, exclude=True)

    @override
    def get_type(self) -> str:
        return "message"

    @override
    def get_message(self) -> Message:
        return self.message


class NoticeEvent(QQEvent):
    """Base class for all inbound QQ notice events."""

    @override
    def get_type(self) -> str:
        return "notice"

    @override
    def get_message(self) -> Message:
        raise ValueError(f"{self.__class__.__name__} has no message.")

    @override
    def is_tome(self) -> bool:
        return False


__all__ = [
    "MessageEvent",
    "MetaEvent",
    "NoticeEvent",
    "QQEvent",
    "ReadyEvent",
    "ResumedEvent",
]
