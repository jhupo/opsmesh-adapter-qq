"""Unit tests for WebSocket frames and Ed25519 Webhook challenge/verification."""

import json

from opsmesh.drivers import Request
from pydantic import SecretStr
import pytest

from qq.config import BotConfig
from qq.transport import (
    Ed25519WebhookSigner,
    GatewayPayload,
    WebhookHandler,
    build_heartbeat_frame,
    build_identify_frame,
    build_resume_frame,
    parse_gateway_payload,
)
from qq.typing import OpCode


def test_ws_protocol_frame_builders() -> None:
    ident = parse_gateway_payload(
        build_identify_frame(access_token="tok", intents=1 << 25, shard=(0, 2))
    )
    assert ident.op == int(OpCode.IDENTIFY)
    assert ident.d["token"] == "QQBot tok"
    assert ident.d["shard"] == [0, 2]

    resume = parse_gateway_payload(
        build_resume_frame(access_token="tok", session_id="sid", seq=42)
    )
    assert resume.op == int(OpCode.RESUME)
    assert resume.d["session_id"] == "sid"
    assert resume.d["seq"] == 42

    hb = parse_gateway_payload(build_heartbeat_frame(42))
    assert hb.op == int(OpCode.HEARTBEAT)
    assert hb.d == 42


@pytest.mark.anyio
async def test_webhook_op13_challenge_and_ed25519_dispatch() -> None:
    bot = BotConfig(
        app_id="102000001",
        app_secret=SecretStr("super_secret_key"),
        transport="webhook",
    )
    dispatched: list[tuple[str, GatewayPayload]] = []

    async def _on_dispatch(app_id: str, payload: GatewayPayload) -> None:
        dispatched.append((app_id, payload))

    handler = WebhookHandler({bot.app_id: bot}, on_dispatch=_on_dispatch)

    # 1. op=13 validation challenge
    challenge_body = json.dumps(
        {
            "op": 13,
            "d": {"plain_token": "hello_token", "event_ts": "1730000000"},
        }
    ).encode("utf-8")
    resp = await handler.handle_http_request(
        Request(
            "POST",
            "http://localhost/qq/webhook",
            headers={"X-Bot-Appid": bot.app_id},
            content=challenge_body,
        )
    )
    assert resp.status_code == 200
    body_json = json.loads(resp.content or "{}")
    assert body_json["plain_token"] == "hello_token"
    assert len(body_json["signature"]) == 128

    # 2. op=0 valid Ed25519 signed dispatch
    signer = Ed25519WebhookSigner("super_secret_key")
    event_body = json.dumps(
        {
            "op": 0,
            "t": "GROUP_AT_MESSAGE_CREATE",
            "id": "ev_1",
            "d": {"id": "m1", "group_openid": "G1", "content": "hi"},
        }
    ).encode("utf-8")
    ts = "1730000001"
    sig = signer._private_key.sign(ts.encode("utf-8") + event_body).hex()

    ok_resp = await handler.handle_http_request(
        Request(
            "POST",
            "http://localhost/qq/webhook",
            headers={
                "X-Bot-Appid": bot.app_id,
                "X-Signature-Ed25519": sig,
                "X-Signature-Timestamp": ts,
            },
            content=event_body,
        )
    )
    assert ok_resp.status_code == 200
    assert len(dispatched) == 1
    assert dispatched[0][0] == bot.app_id
    assert dispatched[0][1].t == "GROUP_AT_MESSAGE_CREATE"

    # 3. Tampered signature -> 403
    bad_resp = await handler.handle_http_request(
        Request(
            "POST",
            "http://localhost/qq/webhook",
            headers={
                "X-Bot-Appid": bot.app_id,
                "X-Signature-Ed25519": "00" * 64,
                "X-Signature-Timestamp": ts,
            },
            content=event_body,
        )
    )
    assert bad_resp.status_code == 403
