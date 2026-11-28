"""QQ Official Bot v1/v2 protocol adapter for OpsMesh."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str | None = version("opsmesh-adapter-qq")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.1.0"


from .adapter import Adapter as Adapter
from .api import MessageStream as MessageStream
from .config import BotConfig as BotConfig
from .config import Config as Config
from .config import IntentConfig as IntentConfig
from .event import AtMessageCreateEvent as AtMessageCreateEvent
from .event import BatchRemoveMembersReturn as BatchRemoveMembersReturn
from .event import C2CMessageCreateEvent as C2CMessageCreateEvent
from .event import C2CMsgReceiveEvent as C2CMsgReceiveEvent
from .event import C2CMsgRejectEvent as C2CMsgRejectEvent
from .event import DirectMessageCreateEvent as DirectMessageCreateEvent
from .event import FriendAddEvent as FriendAddEvent
from .event import FriendDelEvent as FriendDelEvent
from .event import GroupAddRobotEvent as GroupAddRobotEvent
from .event import GroupAtMessageCreateEvent as GroupAtMessageCreateEvent
from .event import GroupBotStateReturn as GroupBotStateReturn
from .event import GroupDelRobotEvent as GroupDelRobotEvent
from .event import GroupInfoReturn as GroupInfoReturn
from .event import GroupJoinRequestEvent as GroupJoinRequestEvent
from .event import GroupMemberAddEvent as GroupMemberAddEvent
from .event import GroupMemberBlacklistReturn as GroupMemberBlacklistReturn
from .event import GroupMemberInfo as GroupMemberInfo
from .event import GroupMemberRemoveEvent as GroupMemberRemoveEvent
from .event import GroupMembersReturn as GroupMembersReturn
from .event import GroupMessageCreateEvent as GroupMessageCreateEvent
from .event import GroupMessageEvent as GroupMessageEvent
from .event import GroupMsgReceiveEvent as GroupMsgReceiveEvent
from .event import GroupMsgRejectEvent as GroupMsgRejectEvent
from .event import GroupNoticeEvent as GroupNoticeEvent
from .event import GroupRestrictChatSettingReturn as GroupRestrictChatSettingReturn
from .event import GuildMessageEvent as GuildMessageEvent
from .event import GuildNoticeEvent as GuildNoticeEvent
from .event import InteractionCreateEvent as InteractionCreateEvent
from .event import JoinRequestItem as JoinRequestItem
from .event import JoinRequestListReturn as JoinRequestListReturn
from .event import MemberBlacklistOpReturn as MemberBlacklistOpReturn
from .event import MessageCreateEvent as MessageCreateEvent
from .event import MessageEvent as MessageEvent
from .event import MetaEvent as MetaEvent
from .event import NoticeEvent as NoticeEvent
from .event import PostC2CMessagesReturn as PostC2CMessagesReturn
from .event import PostFilesReturn as PostFilesReturn
from .event import PostGroupMembersReturn as PostGroupMembersReturn
from .event import PostGroupMessagesReturn as PostGroupMessagesReturn
from .event import QQEvent as QQEvent
from .event import ReadyEvent as ReadyEvent
from .event import ResumedEvent as ResumedEvent
from .event import SetMemberMuteState as SetMemberMuteState
from .event import User as User
from .event import parse_event as parse_event
from .exception import AuditException as AuditException
from .exception import MediaError as MediaError
from .exception import MediaLimitExceeded as MediaLimitExceeded
from .exception import QQActionFailed as QQActionFailed
from .exception import QQAdapterException as QQAdapterException
from .exception import QQNetworkError as QQNetworkError
from .exception import RateLimitException as RateLimitException
from .exception import TokenError as TokenError
from .exception import UnauthorizedException as UnauthorizedException
from .exception import WebhookVerificationError as WebhookVerificationError
from .gateway import Gateway as Gateway
from .message import Message as Message
from .message import MessageSegment as MessageSegment
from .permission import GROUP_ADMIN as GROUP_ADMIN
from .permission import GROUP_OWNER as GROUP_OWNER
from .permission import GUILD_ADMIN as GUILD_ADMIN
from .permission import GUILD_OWNER as GUILD_OWNER
from .typing import ADAPTER_NAME as ADAPTER_NAME
from .typing import Intents as Intents
from .typing import MediaFileType as MediaFileType
from .typing import OpCode as OpCode
from .typing import QQAction as QQAction
from .typing import QQMsgType as QQMsgType
from .typing import StreamState as StreamState
