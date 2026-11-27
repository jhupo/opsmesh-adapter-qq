"""QQ OpenAPI v1/v2 services and declarative ActionDispatcher."""

from .client import ApiClient
from .dispatcher import ActionContext, ActionDispatcher, ActionHandler
from .group_admin import GroupAdminService
from .guild_core import GuildCoreService
from .guild_ext import GuildExtService
from .guild_message import GuildMessageService
from .media import MediaService
from .messaging import MessageStream, MessagingService
from .token import TokenManager

__all__ = [
    "ActionContext",
    "ActionDispatcher",
    "ActionHandler",
    "ApiClient",
    "GroupAdminService",
    "GuildCoreService",
    "GuildExtService",
    "GuildMessageService",
    "MediaService",
    "MessageStream",
    "MessagingService",
    "TokenManager",
]
