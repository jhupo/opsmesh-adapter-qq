"""Outbound QQ message serializer for Group/C2C v2 and Guild v1."""

from dataclasses import dataclass, field

from qq.typing import MediaFileType, QQMsgType, T_JsonDict

from .segment import Message, MessageSegment

_MEDIA_SEGMENT_TYPES: dict[str, MediaFileType] = {
    "image": MediaFileType.IMAGE,
    "video": MediaFileType.VIDEO,
    "audio": MediaFileType.VOICE,
    "file": MediaFileType.FILE,
}


@dataclass(slots=True)
class V2SendUnit:
    """Single Group/C2C v2 HTTP message dispatch unit."""

    msg_type: QQMsgType
    content: str = ""
    markdown: T_JsonDict | None = None
    keyboard: T_JsonDict | None = None
    ark: T_JsonDict | None = None
    media_segment: MessageSegment | None = None
    media_file_type: MediaFileType | None = None
    message_reference: T_JsonDict | None = None

    def to_payload(
        self,
        *,
        file_info: str | None = None,
        msg_id: str | None = None,
        event_id: str | None = None,
        msg_seq: int | None = None,
    ) -> T_JsonDict:
        body: T_JsonDict = {"msg_type": int(self.msg_type)}
        if self.content:
            body["content"] = self.content
        if self.markdown is not None:
            body["markdown"] = self.markdown
        if self.keyboard is not None:
            body["keyboard"] = self.keyboard
        if self.ark is not None:
            body["ark"] = self.ark
        if file_info is not None:
            body["media"] = {"file_info": file_info}
        if self.message_reference is not None:
            body["message_reference"] = self.message_reference
        if msg_id is not None:
            body["msg_id"] = msg_id
        if event_id is not None:
            body["event_id"] = event_id
        if msg_seq is not None:
            body["msg_seq"] = msg_seq
        return body


@dataclass(slots=True)
class GuildSendPayload:
    """Serialized payload for Guild v1 channel / DMS messages."""

    content: str | None = None
    image: str | None = None
    markdown: T_JsonDict | None = None
    keyboard: T_JsonDict | None = None
    ark: T_JsonDict | None = None
    embed: T_JsonDict | None = None
    message_reference: T_JsonDict | None = None
    file_image: tuple[str, bytes] | None = None
    extra: T_JsonDict = field(default_factory=dict)

    def to_body(
        self, *, msg_id: str | None = None, event_id: str | None = None
    ) -> T_JsonDict:
        body: T_JsonDict = dict(self.extra)
        if self.content is not None:
            body["content"] = self.content
        if self.image is not None:
            body["image"] = self.image
        if self.markdown is not None:
            body["markdown"] = self.markdown
        if self.keyboard is not None:
            body["keyboard"] = self.keyboard
        if self.ark is not None:
            body["ark"] = self.ark
        if self.embed is not None:
            body["embed"] = self.embed
        if self.message_reference is not None:
            body["message_reference"] = self.message_reference
        if msg_id is not None:
            body["msg_id"] = msg_id
        if event_id is not None:
            body["event_id"] = event_id
        return body


def plan_v2_units(message: Message, *, auto_markdown: bool = False) -> list[V2SendUnit]:
    """Split a multimodal Message into ordered QQ v2 Group/C2C send units."""
    text_parts: list[str] = []
    markdown_data: T_JsonDict | None = None
    keyboard_data: T_JsonDict | None = None
    ark_data: T_JsonDict | None = None
    reference_data: T_JsonDict | None = None
    media_units: list[V2SendUnit] = []

    for seg in message:
        if seg.type in (
            "text",
            "emoji",
            "mention_user",
            "mention_channel",
            "mention_everyone",
        ):
            text_parts.append(str(seg))
        elif seg.type == "markdown":
            markdown_data = dict(seg.data)
        elif seg.type == "keyboard":
            keyboard_data = dict(seg.data)
        elif seg.type == "ark":
            ark_data = dict(seg.data)
        elif seg.type == "reference":
            reference_data = dict(seg.data)
        elif seg.type in _MEDIA_SEGMENT_TYPES:
            media_units.append(
                V2SendUnit(
                    msg_type=QQMsgType.MEDIA,
                    media_segment=seg,
                    media_file_type=_MEDIA_SEGMENT_TYPES[seg.type],
                )
            )

    units: list[V2SendUnit] = []
    joined_text = "".join(text_parts)

    if markdown_data is not None:
        units.append(
            V2SendUnit(
                msg_type=QQMsgType.MARKDOWN,
                content=joined_text,
                markdown=markdown_data,
                keyboard=keyboard_data,
                message_reference=reference_data,
            )
        )
    elif ark_data is not None:
        units.append(
            V2SendUnit(
                msg_type=QQMsgType.ARK,
                content=joined_text,
                ark=ark_data,
                keyboard=keyboard_data,
                message_reference=reference_data,
            )
        )
    elif joined_text or keyboard_data is not None:
        if auto_markdown and joined_text:
            units.append(
                V2SendUnit(
                    msg_type=QQMsgType.MARKDOWN,
                    markdown={"content": joined_text},
                    keyboard=keyboard_data,
                    message_reference=reference_data,
                )
            )
        else:
            units.append(
                V2SendUnit(
                    msg_type=QQMsgType.TEXT,
                    content=joined_text or " ",
                    keyboard=keyboard_data,
                    message_reference=reference_data,
                )
            )

    units.extend(media_units)
    return units


def serialize_guild_message(message: Message) -> GuildSendPayload:
    """Serialize a Message into a Guild v1 channel/DMS send payload."""
    text_parts: list[str] = []
    payload = GuildSendPayload()

    for seg in message:
        if seg.type in (
            "text",
            "emoji",
            "mention_user",
            "mention_channel",
            "mention_everyone",
        ):
            text_parts.append(str(seg))
        elif seg.type == "image":
            if seg.data.get("url"):
                payload.image = str(seg.data["url"])
            elif isinstance(seg.data.get("content"), (bytes, bytearray)):
                payload.file_image = (
                    str(seg.data.get("filename") or "image.png"),
                    bytes(seg.data["content"]),
                )
        elif seg.type == "markdown":
            payload.markdown = dict(seg.data)
        elif seg.type == "keyboard":
            payload.keyboard = dict(seg.data)
        elif seg.type == "ark":
            payload.ark = dict(seg.data)
        elif seg.type == "embed":
            payload.embed = dict(seg.data)
        elif seg.type == "reference":
            payload.message_reference = dict(seg.data)

    joined = "".join(text_parts)
    if joined:
        payload.content = joined
    return payload


__all__ = [
    "GuildSendPayload",
    "V2SendUnit",
    "plan_v2_units",
    "serialize_guild_message",
]
