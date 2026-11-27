"""QQ Official Bot Adapter: WS sharding, Ed25519 Webhook, and ActionDispatcher."""

from typing import Any
from typing_extensions import override

from opsmesh.adapters import Adapter as BaseAdapter
from opsmesh.adapters import Gateway as BaseGateway
from opsmesh.drivers import (
    URL,
    ASGIMixin,
    Driver,
    HTTPClientMixin,
    HTTPServerSetup,
    WebSocketClientMixin,
)
from opsmesh.message import handle_event
from opsmesh.plugin import get_plugin_config

from qq.api import (
    ActionDispatcher,
    ApiClient,
    GroupAdminService,
    GuildCoreService,
    GuildExtService,
    GuildMessageService,
    MediaService,
    MessagingService,
    TokenManager,
)
from qq.config import BotConfig, Config
from qq.event import (
    C2CMessageCreateEvent,
    GroupMessageEvent,
    MessageEvent,
    ReadyEvent,
    parse_event,
)
from qq.gateway import Gateway
from qq.transport import GatewayPayload, WebhookHandler, WSSession
from qq.typing import ADAPTER_NAME
from qq.utils import DedupeRing, log


class Adapter(BaseAdapter):
    """Native asynchronous QQ Official Bot v1/v2 adapter for OpsMesh."""

    @classmethod
    @override
    def get_name(cls) -> str:
        return ADAPTER_NAME

    @override
    def __init__(
        self,
        driver: Driver,
        *,
        qq_config: Config | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(driver, **kwargs)
        if not isinstance(driver, HTTPClientMixin):
            raise TypeError(
                "QQ Adapter requires HTTPClientMixin "
                "(e.g. DRIVER=~httpx+~websockets or DRIVER=~aiohttp)."
            )

        self.qq_config: Config = (
            qq_config if qq_config is not None else get_plugin_config(Config)
        )
        self._api_client = ApiClient(self, self.qq_config)
        self._messaging = MessagingService(self._api_client)
        self._media = MediaService(self, self._api_client, self.qq_config)
        self._dispatcher = ActionDispatcher(
            messaging=self._messaging,
            media=self._media,
            group_admin=GroupAdminService(self._api_client),
            guild_core=GuildCoreService(self._api_client),
            guild_message=GuildMessageService(self._api_client),
            guild_ext=GuildExtService(self._api_client),
        )

        self._bot_gateways: dict[str, Gateway] = {}
        self._bots_by_appid: dict[str, BotConfig] = {}
        self._token_managers: dict[str, TokenManager] = {}
        self._dedupe_rings: dict[str, DedupeRing] = {}
        self._ws_sessions: list[WSSession] = []
        self._active_shards: dict[str, int] = {}
        self._webhook_handler: WebhookHandler | None = None

        webhook_bots: dict[str, BotConfig] = {}
        for bot_cfg in self.qq_config.qq_bots:
            effective_cfg = (
                bot_cfg.model_copy(update={"is_sandbox": True})
                if self.qq_config.qq_is_sandbox and not bot_cfg.is_sandbox
                else bot_cfg
            )
            gw = Gateway(self, effective_cfg)
            self._bot_gateways[gw.id] = gw
            self._bots_by_appid[effective_cfg.app_id] = effective_cfg
            self._token_managers[gw.id] = TokenManager(
                self, effective_cfg, timeout=self.qq_config.qq_timeout
            )
            self._dedupe_rings[gw.id] = DedupeRing(
                capacity=self.qq_config.qq_dedupe_capacity,
                ttl=self.qq_config.qq_dedupe_ttl,
            )
            self._active_shards[gw.id] = 0
            if effective_cfg.transport == "webhook":
                webhook_bots[effective_cfg.app_id] = effective_cfg

        if webhook_bots:
            self._webhook_handler = WebhookHandler(
                webhook_bots,
                on_dispatch=self._on_webhook_dispatch,
                max_body_bytes=self.qq_config.qq_webhook_max_body_bytes,
            )
            if isinstance(driver, ASGIMixin):
                self.setup_http_server(
                    HTTPServerSetup(
                        path=URL(self.qq_config.qq_webhook_path),
                        method="POST",
                        name="qq_webhook",
                        handle_func=self._webhook_handler.handle_http_request,
                    )
                )

        self.driver.on_startup(self._startup)
        self.driver.on_shutdown(self._shutdown)

    async def _startup(self) -> None:
        if not self._bot_gateways:
            log("WARNING", "No QQ bots configured in QQ_BOTS.")
            return

        for gw in self._bot_gateways.values():
            cfg = gw.bot_config
            if cfg.transport == "webhook":
                if gw.id not in self.gateways:
                    self.connect(gw)
                continue

            if not isinstance(self.driver, WebSocketClientMixin):
                raise TypeError(
                    "QQ WebSocket transport requires WebSocketClientMixin "
                    "(e.g. DRIVER=~httpx+~websockets or DRIVER=~aiohttp)."
                )

            token_mgr = self._token_managers[gw.id]
            ws_url: str | None = None
            shards: list[tuple[int, int]]
            if cfg.shard is not None:
                shards = [cfg.shard]
            else:
                shard_info = await self._messaging.shard_url_get(
                    bot_config=cfg, token_manager=token_mgr
                )
                ws_url = shard_info.url
                count = max(shard_info.shards, 1)
                shards = [(i, count) for i in range(count)]

            for shard in shards:
                session = WSSession(
                    self,
                    cfg,
                    token_mgr,
                    shard=shard,
                    gateway_url=ws_url,
                    on_dispatch=self._make_ws_dispatch_cb(gw),
                    on_ready=self._make_shard_ready_cb(gw),
                    on_disconnected=self._make_shard_disconnected_cb(gw),
                )
                self._ws_sessions.append(session)
                self.driver.task_group.start_soon(session.run)

    async def _shutdown(self) -> None:
        for session in self._ws_sessions:
            session.stop()
        for session in self._ws_sessions:
            await session.wait_closed()
        for gw in list(self.gateways.values()):
            self.disconnect(gw)

    def _make_shard_ready_cb(self, gateway: Gateway):
        def _cb() -> None:
            self._active_shards[gateway.id] = self._active_shards.get(gateway.id, 0) + 1
            if gateway.id not in self.gateways:
                self.connect(gateway)

        return _cb

    def _make_shard_disconnected_cb(self, gateway: Gateway):
        def _cb() -> None:
            remaining = max(self._active_shards.get(gateway.id, 1) - 1, 0)
            self._active_shards[gateway.id] = remaining
            if remaining == 0 and gateway.id in self.gateways:
                self.disconnect(gateway)

        return _cb

    def _make_ws_dispatch_cb(self, gateway: Gateway):
        async def _cb(payload: GatewayPayload) -> None:
            await self.handle_dispatch_payload(gateway, payload)

        return _cb

    async def _on_webhook_dispatch(self, app_id: str, payload: GatewayPayload) -> None:
        gw = self._bot_gateways.get(f"qq:{app_id}")
        if gw is not None:
            await self.handle_dispatch_payload(gw, payload)

    async def handle_dispatch_payload(
        self, gateway: Gateway, payload: GatewayPayload
    ) -> None:
        """Deduplicate, parse, track passive reply window, and dispatch to OpsMesh."""
        event_type = payload.t or ""
        if not event_type:
            return

        dedupe_key = payload.id or (
            str(payload.d.get("id"))
            if isinstance(payload.d, dict) and payload.d.get("id")
            else ""
        )
        if dedupe_key and self._dedupe_rings[gateway.id].seen_or_record(dedupe_key):
            log("DEBUG", f"Dropped duplicate QQ event {dedupe_key!r}")
            return

        bot_user_id = gateway.self_info.id if gateway.self_info else None
        event = parse_event(
            event_type,
            payload.d,
            event_id=payload.id,
            bot_user_id=bot_user_id,
        )
        if isinstance(event, ReadyEvent):
            gateway.self_info = event.user
        elif isinstance(event, MessageEvent) and event.id:
            if isinstance(event, C2CMessageCreateEvent):
                gateway.passive_tracker.register(event.id, is_c2c=True)
            elif isinstance(event, GroupMessageEvent):
                gateway.passive_tracker.register(event.id, is_c2c=False)

        self.driver.task_group.start_soon(handle_event, gateway, event)

    @override
    async def _invoke(
        self,
        gateway: BaseGateway,
        action: str,
        **params: Any,
    ) -> Any:
        if not isinstance(gateway, Gateway):
            raise TypeError(f"Expected qq.Gateway, got {type(gateway).__name__}")
        return await self._dispatcher.dispatch(
            bot_config=gateway.bot_config,
            token_manager=self._token_managers[gateway.id],
            action=action,
            params=params,
        )


__all__ = ["Adapter"]
