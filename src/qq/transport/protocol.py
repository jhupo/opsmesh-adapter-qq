"""QQ Gateway OpCode frame schema and frame builders."""

import json
from typing import Any

from pydantic import BaseModel, ConfigDict

from qq.typing import OpCode, T_JsonDict


class GatewayPayload(BaseModel):
    """Standard QQ Gateway WebSocket / Webhook JSON payload."""

    model_config = ConfigDict(extra="allow")

    op: int
    d: Any = None
    s: int | None = None
    t: str | None = None
    id: str | None = None


def parse_gateway_payload(raw: str | bytes) -> GatewayPayload:
    """Decode a raw JSON frame into a GatewayPayload."""
    data = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
    return GatewayPayload.model_validate(data)


def build_identify_frame(
    *,
    access_token: str,
    intents: int,
    shard: tuple[int, int] = (0, 1),
) -> str:
    """Build OP_IDENTIFY (op=2) JSON frame."""
    body: T_JsonDict = {
        "op": int(OpCode.IDENTIFY),
        "d": {
            "token": f"QQBot {access_token}",
            "intents": intents,
            "shard": [shard[0], shard[1]],
            "properties": {
                "$os": "python",
                "$browser": "opsmesh",
                "$device": "opsmesh",
            },
        },
    }
    return json.dumps(body, separators=(",", ":"))


def build_resume_frame(
    *,
    access_token: str,
    session_id: str,
    seq: int,
) -> str:
    """Build OP_RESUME (op=6) JSON frame."""
    body: T_JsonDict = {
        "op": int(OpCode.RESUME),
        "d": {
            "token": f"QQBot {access_token}",
            "session_id": session_id,
            "seq": seq,
        },
    }
    return json.dumps(body, separators=(",", ":"))


def build_heartbeat_frame(seq: int | None) -> str:
    """Build OP_HEARTBEAT (op=1) JSON frame."""
    return json.dumps({"op": int(OpCode.HEARTBEAT), "d": seq}, separators=(",", ":"))


__all__ = [
    "GatewayPayload",
    "build_heartbeat_frame",
    "build_identify_frame",
    "build_resume_frame",
    "parse_gateway_payload",
]
