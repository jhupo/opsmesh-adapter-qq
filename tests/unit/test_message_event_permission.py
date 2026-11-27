"""Unit tests for QQ message parsing, serialization, events, permissions, and utils."""

from unittest.mock import MagicMock

import pytest

from qq import (
    GROUP_ADMIN,
    GROUP_OWNER,
    GUILD_ADMIN,
    GUILD_OWNER,
    C2CMessageCreateEvent,
    GroupAtMessageCreateEvent,
    GroupJoinRequestEvent,
    InteractionCreateEvent,
    MediaError,
    Message,
    MessageSegment,
    QQAdapterException,
    QQMsgType,
    parse_event,
)
from qq.message import parse_inbound_message, plan_v2_units
from qq.utils import (
    DedupeRing,
    PassiveReplyTracker,
    validate_media_url,
    validate_qq_identifier,
)


def test_parse_inbound_message_strips_bot_mention_and_tags() -> None:
    msg = parse_inbound_message(
        "<@!bot_1> /mute <@!u_2> <emoji:14> <#ch_1> @everyone",
        attachments=[
            {
                "url": "cdn.qpic.cn/test.png",
                "content_type": "image/png",
                "filename": "test.png",
            }
        ],
        strip_leading_bot_id="bot_1",
    )
    assert msg.extract_plain_text().startswith("/mute")
    types = [seg.type for seg in msg]
    assert "mention_user" in types
    assert "emoji" in types
    assert "mention_channel" in types
    assert "mention_everyone" in types
    assert "image" in types
    img = next(seg for seg in msg if seg.type == "image")
    assert img.data["url"] == "https://cdn.qpic.cn/test.png"


def test_plan_v2_units_combines_markdown_keyboard_and_isolates_media() -> None:
    msg = (
        MessageSegment.markdown("# Title")
        + MessageSegment.keyboard(id="kb_1")
        + MessageSegment.image(url="https://cdn.qpic.cn/a.png")
    )
    units = plan_v2_units(msg)
    assert len(units) == 2
    assert units[0].msg_type == QQMsgType.MARKDOWN
    assert units[0].keyboard == {"id": "kb_1"}
    assert units[1].msg_type == QQMsgType.MEDIA
    assert units[1].media_segment is not None


@pytest.mark.anyio
async def test_group_and_guild_permissions() -> None:
    gw = MagicMock()
    owner_ev = parse_event(
        "GROUP_AT_MESSAGE_CREATE",
        {
            "id": "m1",
            "group_openid": "G1",
            "content": "hello",
            "author": {"member_openid": "U1", "member_role": "owner"},
        },
    )
    admin_ev = parse_event(
        "GROUP_AT_MESSAGE_CREATE",
        {
            "id": "m2",
            "group_openid": "G1",
            "content": "hello",
            "author": {"member_openid": "U2", "member_role": "admin"},
        },
    )
    guild_ev = parse_event(
        "AT_MESSAGE_CREATE",
        {
            "id": "gm1",
            "guild_id": "G1",
            "channel_id": "C1",
            "content": "hi",
            "author": {"id": "U3"},
            "member": {"roles": ["4", "2"]},
        },
    )
    assert isinstance(owner_ev, GroupAtMessageCreateEvent)
    assert await GROUP_OWNER(gw, owner_ev)
    assert not await GROUP_ADMIN(gw, owner_ev)
    assert await GROUP_ADMIN(gw, admin_ev)
    assert not await GROUP_OWNER(gw, admin_ev)
    assert await GUILD_OWNER(gw, guild_ev)
    assert await GUILD_ADMIN(gw, guild_ev)


def test_parse_event_variants() -> None:
    c2c = parse_event(
        "C2C_MESSAGE_CREATE",
        {"id": "c1", "content": "hi", "author": {"user_openid": "U_C2C"}},
    )
    assert isinstance(c2c, C2CMessageCreateEvent)
    assert c2c.get_user_id() == "U_C2C"
    assert c2c.is_tome()

    req = parse_event(
        "GROUP_JOIN_REQUEST",
        {
            "group_openid": "G1",
            "join_request_id": "JR1",
            "member_openid": "U9",
            "verify_info": "secret",
        },
    )
    assert isinstance(req, GroupJoinRequestEvent)
    assert req.join_request_id == "JR1"

    inter = parse_event(
        "INTERACTION_CREATE",
        {
            "id": "I1",
            "group_openid": "G1",
            "group_member_openid": "U9",
            "data": {"resolved": {"button_data": "approve:JR1"}},
        },
    )
    assert isinstance(inter, InteractionCreateEvent)
    assert inter.button_data == "approve:JR1"


@pytest.mark.anyio
async def test_passive_reply_tracker_and_validators() -> None:
    tracker = PassiveReplyTracker()
    tracker.register("msg_1", is_c2c=False, max_replies=2)
    assert await tracker.allocate_seq("msg_1") == 1
    assert await tracker.allocate_seq("msg_1") == 2
    assert await tracker.allocate_seq("msg_1") is None

    ring = DedupeRing(capacity=4, ttl=60.0)
    assert not ring.seen_or_record("k1")
    assert ring.seen_or_record("k1")

    assert validate_qq_identifier("GROUP_OPENID_01") == "GROUP_OPENID_01"
    with pytest.raises(QQAdapterException):
        validate_qq_identifier("../evil")

    assert validate_media_url("https://cdn.qpic.cn/img.png").startswith("https://")
    with pytest.raises(MediaError):
        validate_media_url("http://127.0.0.1/secret")
    with pytest.raises(MediaError):
        validate_media_url("https://evil.example.com/img.png")

    assert str(Message("abc")) == "abc"
