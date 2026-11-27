"""Interactive button callback event (INTERACTION_CREATE)."""

from typing import Any
from typing_extensions import override

from pydantic import Field

from .base import NoticeEvent
from .models import QQModel


class InteractionData(QQModel):
    resolved: dict[str, Any] = Field(default_factory=dict)
    type: int = 0


class InteractionCreateEvent(NoticeEvent):
    """Inbound interactive keyboard button callback (INTERACTION_CREATE)."""

    id: str = ""
    type: int = 11
    scene: str = ""
    chat_type: int = 0
    timestamp: str | int = ""
    guild_id: str | None = None
    channel_id: str | None = None
    group_openid: str | None = None
    group_member_openid: str | None = None
    user_openid: str | None = None
    data: InteractionData = Field(default_factory=InteractionData)

    @property
    def button_data(self) -> str:
        return str(self.data.resolved.get("button_data") or "")

    @property
    def button_id(self) -> str:
        return str(self.data.resolved.get("button_id") or "")

    @override
    def get_event_name(self) -> str:
        return "notice.interaction_create"

    @override
    def get_event_description(self) -> str:
        return (
            f"InteractionCreate {self.id} scene={self.scene} data={self.button_data!r}"
        )

    @override
    def get_user_id(self) -> str:
        return (
            self.group_member_openid
            or self.user_openid
            or str(self.data.resolved.get("user_id") or "")
        )

    @override
    def get_session_id(self) -> str:
        if self.group_openid:
            return f"group_{self.group_openid}_{self.get_user_id()}"
        if self.guild_id:
            return f"guild_{self.guild_id}_{self.channel_id or ''}_{self.get_user_id()}"
        return f"c2c_{self.get_user_id()}"


__all__ = ["InteractionCreateEvent", "InteractionData"]
