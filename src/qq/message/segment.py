"""QQ Official Bot Message and MessageSegment inheriting OpsMesh primitives."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any
from typing_extensions import override

from opsmesh.adapters import Message as BaseMessage
from opsmesh.adapters import MessageSegment as BaseMessageSegment


class MessageSegment(BaseMessageSegment["Message"]):
    """Multimodal QQ Official Bot message segment."""

    @classmethod
    @override
    def get_message_class(cls) -> type["Message"]:
        return Message

    @override
    def __str__(self) -> str:
        match self.type:
            case "text":
                return str(self.data.get("text", ""))
            case "emoji":
                return f"<emoji:{self.data.get('id', '')}>"
            case "mention_user":
                return f"<@!{self.data.get('user_id', '')}>"
            case "mention_channel":
                return f"<#{self.data.get('channel_id', '')}>"
            case "mention_everyone":
                return "@everyone"
            case "markdown":
                return str(
                    self.data.get("content")
                    or self.data.get("custom_template_id")
                    or "[markdown]"
                )
            case _:
                label = (
                    self.data.get("filename")
                    or self.data.get("url")
                    or self.data.get("file_info")
                    or ""
                )
                return f"[{self.type}:{label}]" if label else f"[{self.type}]"

    @override
    def is_text(self) -> bool:
        return self.type == "text"

    @classmethod
    def text(cls, text: str) -> "MessageSegment":
        return cls("text", {"text": text})

    @classmethod
    def emoji(cls, emoji_id: str) -> "MessageSegment":
        return cls("emoji", {"id": str(emoji_id)})

    @classmethod
    def mention_user(cls, user_id: str) -> "MessageSegment":
        return cls("mention_user", {"user_id": str(user_id)})

    @classmethod
    def mention_channel(cls, channel_id: str) -> "MessageSegment":
        return cls("mention_channel", {"channel_id": str(channel_id)})

    @classmethod
    def mention_everyone(cls) -> "MessageSegment":
        return cls("mention_everyone", {})

    @classmethod
    def image(
        cls,
        *,
        url: str | None = None,
        path: str | Path | None = None,
        content: bytes | None = None,
        file_info: str | None = None,
        filename: str = "image.png",
    ) -> "MessageSegment":
        return cls(
            "image",
            {
                "url": url,
                "path": str(path) if path is not None else None,
                "content": content,
                "file_info": file_info,
                "filename": filename,
            },
        )

    @classmethod
    def audio(
        cls,
        *,
        url: str | None = None,
        path: str | Path | None = None,
        content: bytes | None = None,
        file_info: str | None = None,
        filename: str = "voice.silk",
    ) -> "MessageSegment":
        return cls(
            "audio",
            {
                "url": url,
                "path": str(path) if path is not None else None,
                "content": content,
                "file_info": file_info,
                "filename": filename,
            },
        )

    @classmethod
    def video(
        cls,
        *,
        url: str | None = None,
        path: str | Path | None = None,
        content: bytes | None = None,
        file_info: str | None = None,
        filename: str = "video.mp4",
    ) -> "MessageSegment":
        return cls(
            "video",
            {
                "url": url,
                "path": str(path) if path is not None else None,
                "content": content,
                "file_info": file_info,
                "filename": filename,
            },
        )

    @classmethod
    def file(
        cls,
        *,
        url: str | None = None,
        path: str | Path | None = None,
        content: bytes | None = None,
        file_info: str | None = None,
        filename: str | None = None,
    ) -> "MessageSegment":
        resolved = filename or (Path(path).name if path is not None else "file.bin")
        return cls(
            "file",
            {
                "url": url,
                "path": str(path) if path is not None else None,
                "content": content,
                "file_info": file_info,
                "filename": resolved,
            },
        )

    @classmethod
    def attachment(
        cls,
        *,
        url: str,
        content_type: str = "",
        filename: str = "",
        size: int | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> "MessageSegment":
        return cls(
            "attachment",
            {
                "url": url,
                "content_type": content_type,
                "filename": filename,
                "size": size,
                "width": width,
                "height": height,
            },
        )

    @classmethod
    def markdown(
        cls,
        content: str | None = None,
        *,
        custom_template_id: str | None = None,
        params: list[dict[str, Any]] | None = None,
    ) -> "MessageSegment":
        payload: dict[str, Any] = {}
        if content is not None:
            payload["content"] = content
        if custom_template_id is not None:
            payload["custom_template_id"] = custom_template_id
        if params is not None:
            payload["params"] = params
        return cls("markdown", payload)

    @classmethod
    def keyboard(
        cls,
        *,
        id: str | None = None,
        content: dict[str, Any] | None = None,
    ) -> "MessageSegment":
        payload: dict[str, Any] = {}
        if id is not None:
            payload["id"] = id
        if content is not None:
            payload["content"] = content
        return cls("keyboard", payload)

    @classmethod
    def ark(cls, template_id: int, kv: list[dict[str, Any]]) -> "MessageSegment":
        return cls("ark", {"template_id": template_id, "kv": kv})

    @classmethod
    def embed(cls, embed: dict[str, Any]) -> "MessageSegment":
        return cls("embed", dict(embed))

    @classmethod
    def reference(
        cls, message_id: str, *, ignore_get_message_error: bool = True
    ) -> "MessageSegment":
        return cls(
            "reference",
            {
                "message_id": message_id,
                "ignore_get_message_error": ignore_get_message_error,
            },
        )


class Message(BaseMessage[MessageSegment]):
    """QQ Official Bot multimodal message sequence."""

    @classmethod
    @override
    def get_segment_class(cls) -> type[MessageSegment]:
        return MessageSegment

    @staticmethod
    @override
    def _construct(msg: str) -> Iterable[MessageSegment]:
        yield MessageSegment.text(msg)


__all__ = ["Message", "MessageSegment"]
