"""WebSocket shard session with heartbeat, OP_RESUME, and exponential backoff."""

from collections.abc import Awaitable, Callable
import random
from typing import TYPE_CHECKING

import anyio
from opsmesh.drivers import Request, WebSocket

from qq.config import BotConfig
from qq.typing import OpCode
from qq.utils import log

from .protocol import (
    GatewayPayload,
    build_heartbeat_frame,
    build_identify_frame,
    build_resume_frame,
    parse_gateway_payload,
)

if TYPE_CHECKING:
    from qq.adapter import Adapter
    from qq.api.token import TokenManager

DispatchCallback = Callable[[GatewayPayload], Awaitable[None]]
LifecycleCallback = Callable[[], None]


class WSSession:
    """Managed WebSocket connection for one QQ bot shard."""

    def __init__(
        self,
        adapter: "Adapter",
        bot_config: BotConfig,
        token_manager: "TokenManager",
        *,
        shard: tuple[int, int] = (0, 1),
        gateway_url: str | None = None,
        on_dispatch: DispatchCallback,
        on_ready: LifecycleCallback | None = None,
        on_disconnected: LifecycleCallback | None = None,
    ) -> None:
        self._adapter = adapter
        self._bot_config = bot_config
        self._token_manager = token_manager
        self.shard: tuple[int, int] = shard
        self._gateway_url: str | None = gateway_url
        self._on_dispatch = on_dispatch
        self._on_ready = on_ready
        self._on_disconnected = on_disconnected

        self.session_id: str | None = None
        self.last_seq: int | None = None
        self._stopped = False
        self._closed_event = anyio.Event()
        self._cancel_scope: anyio.CancelScope | None = None

    def stop(self) -> None:
        """Request graceful termination of this WebSocket shard session."""
        self._stopped = True
        if self._cancel_scope is not None:
            self._cancel_scope.cancel()

    async def wait_closed(self) -> None:
        """Wait until the session loop has exited cleanly."""
        await self._closed_event.wait()

    async def run(self) -> None:
        """Run the reconnect loop until stopped."""
        backoff = 1.0
        try:
            while not self._stopped:
                try:
                    with anyio.CancelScope() as scope:
                        self._cancel_scope = scope
                        await self._run_once()
                    backoff = 1.0
                except anyio.get_cancelled_exc_class():
                    break
                except Exception as exc:
                    log(
                        "WARNING",
                        f"QQ WS shard {self.shard} error "
                        f"({self._bot_config.app_id}): {exc}",
                    )
                finally:
                    self._cancel_scope = None
                    if self._on_disconnected is not None:
                        self._on_disconnected()

                if self._stopped:
                    break
                delay = min(backoff, 30.0) + random.uniform(0.0, 0.5)  # noqa: S311
                await anyio.sleep(delay)
                backoff = min(backoff * 2.0, 30.0)
        finally:
            self._closed_event.set()

    async def _run_once(self) -> None:
        token = await self._token_manager.get_token()
        ws_url = self._gateway_url
        if not ws_url:
            info = await self._adapter._messaging.shard_url_get(
                bot_config=self._bot_config,
                token_manager=self._token_manager,
            )
            ws_url = info.url

        async with self._adapter.websocket(Request("GET", ws_url)) as ws:
            raw_hello = await ws.receive()
            hello = parse_gateway_payload(raw_hello)
            if hello.op != int(OpCode.HELLO) or not isinstance(hello.d, dict):
                raise RuntimeError(f"Expected OP_HELLO, got op={hello.op}")
            interval_ms = int(hello.d.get("heartbeat_interval", 41250))

            if self.session_id and self.last_seq is not None:
                await ws.send_text(
                    build_resume_frame(
                        access_token=token,
                        session_id=self.session_id,
                        seq=self.last_seq,
                    )
                )
            else:
                await ws.send_text(
                    build_identify_frame(
                        access_token=token,
                        intents=self._bot_config.intent.to_int(),
                        shard=self.shard,
                    )
                )

            await self._pump_connection(ws, interval_ms / 1000.0)

    async def _pump_connection(self, ws: WebSocket, heartbeat_interval: float) -> None:
        ack_received = True

        async def _heartbeat_loop() -> None:
            nonlocal ack_received
            while not self._stopped:
                await anyio.sleep(heartbeat_interval)
                if not ack_received:
                    log(
                        "WARNING",
                        f"QQ WS shard {self.shard} heartbeat ACK timeout; reconnect.",
                    )
                    await ws.close()
                    return
                ack_received = False
                await ws.send_text(build_heartbeat_frame(self.last_seq))

        async with anyio.create_task_group() as tg:
            tg.start_soon(_heartbeat_loop)
            try:
                while not self._stopped:
                    raw = await ws.receive()
                    payload = parse_gateway_payload(raw)
                    if payload.s is not None:
                        self.last_seq = payload.s

                    if payload.op == int(OpCode.DISPATCH):
                        if payload.t == "READY" and isinstance(payload.d, dict):
                            sid = payload.d.get("session_id")
                            if isinstance(sid, str) and sid:
                                self.session_id = sid
                            if self._on_ready is not None:
                                self._on_ready()
                        elif payload.t == "RESUMED":
                            if self._on_ready is not None:
                                self._on_ready()
                        await self._on_dispatch(payload)
                    elif payload.op == int(OpCode.HEARTBEAT):
                        await ws.send_text(build_heartbeat_frame(self.last_seq))
                    elif payload.op == int(OpCode.HEARTBEAT_ACK):
                        ack_received = True
                    elif payload.op == int(OpCode.RECONNECT):
                        log("INFO", f"QQ WS shard {self.shard} received OP_RECONNECT.")
                        return
                    elif payload.op == int(OpCode.INVALID_SESSION):
                        log(
                            "WARNING",
                            f"QQ WS shard {self.shard} received OP_INVALID_SESSION; "
                            "clearing session_id.",
                        )
                        self.session_id = None
                        self.last_seq = None
                        return
            finally:
                tg.cancel_scope.cancel()


__all__ = ["DispatchCallback", "LifecycleCallback", "WSSession"]
