"""Runnable OpsMesh example using opsmesh-adapter-qq."""

import opsmesh
from opsmesh import on_command
from opsmesh.rule import to_me

from qq import Adapter, Gateway, MessageEvent


def main() -> None:
    opsmesh.init()
    driver = opsmesh.get_driver()
    driver.register_adapter(Adapter)

    ping = on_command("ping", rule=to_me(), priority=10, block=True)

    @ping.handle()
    async def _handle_ping(gateway: Gateway, event: MessageEvent) -> None:
        await gateway.send(event, "pong (QQ Official Bot)")

    opsmesh.run()


if __name__ == "__main__":
    main()
