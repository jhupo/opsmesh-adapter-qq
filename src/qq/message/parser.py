"""Inbound QQ message content & attachment parser."""

from collections.abc import Mapping, Sequence
import re
from typing import Any

from .segment import Message, MessageSegment

_TAG_RE = re.compile(
    r"(?P<mention><@!?(?P<uid>[^>]+)>)"
    r"|(?P<channel><#(?P<cid>[^>]+)>)"
    r"|(?P<emoji><emoji:(?P<eid>[^>]+)>)"
    r"|(?P<everyone>@everyone)"
)


def parse_inbound_message(
    content: str = "",
    *,
    attachments: Sequence[Mapping[str, Any]] | None = None,
    strip_leading_bot_id: str | None = None,
) -> Message:
    """Parse QQ text content and attachments into an OpsMesh Message."""
    text = content or ""
    if strip_leading_bot_id:
        prefix_re = re.compile(
            rf"^\s*<@!?{re.escape(strip_leading_bot_id)}>\s*",
        )
        text = prefix_re.sub("", text, count=1)
    else:
        text = text.lstrip() if text.startswith(" ") else text

    segments: list[MessageSegment] = []
    pos = 0
    for match in _TAG_RE.finditer(text):
        start, end = match.span()
        if start > pos:
            segments.append(MessageSegment.text(text[pos:start]))
        if match.group("mention"):
            segments.append(MessageSegment.mention_user(match.group("uid")))
        elif match.group("channel"):
            segments.append(MessageSegment.mention_channel(match.group("cid")))
        elif match.group("emoji"):
            segments.append(MessageSegment.emoji(match.group("eid")))
        elif match.group("everyone"):
            segments.append(MessageSegment.mention_everyone())
        pos = end
    if pos < len(text):
        segments.append(MessageSegment.text(text[pos:]))

    for att in attachments or ():
        url = str(att.get("url") or "")
        if url and not url.startswith(("http://", "https://")):
            url = f"https://{url.lstrip('/')}"
        content_type = str(att.get("content_type") or "")
        filename = str(att.get("filename") or "")
        size = att.get("size")
        width = att.get("width")
        height = att.get("height")
        if content_type.startswith("image/"):
            segments.append(
                MessageSegment.image(
                    url=url or None,
                    filename=filename or "image.png",
                )
            )
        else:
            segments.append(
                MessageSegment.attachment(
                    url=url,
                    content_type=content_type,
                    filename=filename,
                    size=int(size) if isinstance(size, int) else None,
                    width=int(width) if isinstance(width, int) else None,
                    height=int(height) if isinstance(height, int) else None,
                )
            )

    return Message(segments)


__all__ = ["parse_inbound_message"]
