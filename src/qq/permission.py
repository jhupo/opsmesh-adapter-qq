"""Zero-I/O OpsMesh Permission primitives for QQ Group and Guild roles."""

from opsmesh.adapters import Event
from opsmesh.permission import Permission

from qq.event import GroupMessageEvent, GuildMessageEvent

GUILD_OWNER_ROLE_ID = "4"
GUILD_ADMIN_ROLE_ID = "2"
GUILD_CHANNEL_ADMIN_ROLE_ID = "5"


async def _group_owner(event: Event) -> bool:
    return (
        isinstance(event, GroupMessageEvent)
        and str(event.author.member_role).lower() == "owner"
    )


async def _group_admin(event: Event) -> bool:
    return (
        isinstance(event, GroupMessageEvent)
        and str(event.author.member_role).lower() == "admin"
    )


async def _guild_owner(event: Event) -> bool:
    return (
        isinstance(event, GuildMessageEvent)
        and event.member is not None
        and GUILD_OWNER_ROLE_ID in event.member.roles
    )


async def _guild_admin(event: Event) -> bool:
    return (
        isinstance(event, GuildMessageEvent)
        and event.member is not None
        and bool(
            set(event.member.roles) & {GUILD_ADMIN_ROLE_ID, GUILD_CHANNEL_ADMIN_ROLE_ID}
        )
    )


GROUP_OWNER: Permission = Permission(_group_owner)
GROUP_ADMIN: Permission = Permission(_group_admin)
GUILD_OWNER: Permission = Permission(_guild_owner)
GUILD_ADMIN: Permission = Permission(_guild_admin)

__all__ = [
    "GROUP_ADMIN",
    "GROUP_OWNER",
    "GUILD_ADMIN",
    "GUILD_OWNER",
]
