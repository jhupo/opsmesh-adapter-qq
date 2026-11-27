"""Dual-mode transport package (WebSocket sharding + Ed25519 Webhook)."""

from .protocol import (
    GatewayPayload,
    build_heartbeat_frame,
    build_identify_frame,
    build_resume_frame,
    parse_gateway_payload,
)
from .webhook import Ed25519WebhookSigner, WebhookHandler
from .ws_session import WSSession

__all__ = [
    "Ed25519WebhookSigner",
    "GatewayPayload",
    "WSSession",
    "WebhookHandler",
    "build_heartbeat_frame",
    "build_identify_frame",
    "build_resume_frame",
    "parse_gateway_payload",
]
