"""HTTP Webhook handler with Ed25519 signature verification and op=13 challenge."""

from collections.abc import Awaitable, Callable
import json
from typing import Any

from opsmesh.drivers import Request, Response

from qq.config import BotConfig
from qq.exception import WebhookVerificationError
from qq.typing import OpCode
from qq.utils import derive_ed25519_seed

from .protocol import GatewayPayload, parse_gateway_payload

WebhookDispatchCallback = Callable[[str, GatewayPayload], Awaitable[None]]


class Ed25519WebhookSigner:
    """Ed25519 signer/verifier derived from QQ Bot app_secret."""

    def __init__(self, app_secret: str) -> None:
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import (
                Ed25519PrivateKey,
            )
        except ImportError as exc:  # pragma: no cover
            raise WebhookVerificationError(
                "Webhook Ed25519 verification requires 'cryptography' "
                "(install opsmesh-adapter-qq[webhook])."
            ) from exc

        seed = derive_ed25519_seed(app_secret)
        self._private_key = Ed25519PrivateKey.from_private_bytes(seed)
        self._public_key = self._private_key.public_key()

    def sign_challenge(self, *, event_ts: str, plain_token: str) -> str:
        """Sign QQ op=13 webhook validation challenge and return hex signature."""
        msg = f"{event_ts}{plain_token}".encode()
        return self._private_key.sign(msg).hex()

    def verify_request(
        self,
        *,
        signature_hex: str,
        timestamp: str,
        raw_body: bytes,
    ) -> bool:
        """Verify X-Signature-Ed25519 over (timestamp + raw_body)."""
        if not signature_hex or not timestamp:
            return False
        try:
            sig_bytes = bytes.fromhex(signature_hex)
            self._public_key.verify(sig_bytes, timestamp.encode("utf-8") + raw_body)
            return True
        except Exception:
            return False


class WebhookHandler:
    """ASGI HTTP handler for QQ Official Bot Webhook callbacks."""

    def __init__(
        self,
        bots: dict[str, BotConfig],
        *,
        on_dispatch: WebhookDispatchCallback,
        max_body_bytes: int = 1024 * 1024,
    ) -> None:
        self._bots = bots
        self._signers: dict[str, Ed25519WebhookSigner] = {}
        self._on_dispatch = on_dispatch
        self._max_body_bytes = max_body_bytes

    def _get_signer(self, app_id: str) -> Ed25519WebhookSigner | None:
        bot = self._bots.get(app_id)
        if bot is None:
            return None
        signer = self._signers.get(app_id)
        if signer is None:
            signer = Ed25519WebhookSigner(bot.app_secret.get_secret_value())
            self._signers[app_id] = signer
        return signer

    async def handle_http_request(self, request: Request) -> Response:
        """Process POST /qq/webhook for op=13 verification and op=0 events."""
        raw_content = request.content
        if isinstance(raw_content, str):
            raw_body = raw_content.encode("utf-8")
        elif isinstance(raw_content, (bytes, bytearray)):
            raw_body = bytes(raw_content)
        else:
            raw_body = b""

        if len(raw_body) > self._max_body_bytes:
            return Response(413, content="Payload too large")

        headers = {k.lower(): v for k, v in request.headers.items()}
        app_id = headers.get("x-bot-appid", "")
        if not app_id and len(self._bots) == 1:
            app_id = next(iter(self._bots))

        signer = self._get_signer(app_id)
        if signer is None:
            return Response(403, content="Unknown X-Bot-Appid")

        try:
            payload = parse_gateway_payload(raw_body)
        except Exception:
            return Response(400, content="Invalid JSON payload")

        if payload.op == int(OpCode.WEBHOOK_VERIFY):
            data: dict[str, Any] = payload.d if isinstance(payload.d, dict) else {}
            plain_token = str(data.get("plain_token") or "")
            event_ts = str(data.get("event_ts") or "")
            if not plain_token or not event_ts:
                return Response(400, content="Missing plain_token or event_ts")
            signature = signer.sign_challenge(
                event_ts=event_ts, plain_token=plain_token
            )
            return Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps(
                    {"plain_token": plain_token, "signature": signature}
                ),
            )

        sig_hex = headers.get("x-signature-ed25519", "")
        ts = headers.get("x-signature-timestamp", "")
        if not signer.verify_request(
            signature_hex=sig_hex, timestamp=ts, raw_body=raw_body
        ):
            return Response(403, content="Invalid Ed25519 signature")

        if payload.op == int(OpCode.DISPATCH):
            await self._on_dispatch(app_id, payload)

        return Response(200, content="")


__all__ = ["Ed25519WebhookSigner", "WebhookDispatchCallback", "WebhookHandler"]
