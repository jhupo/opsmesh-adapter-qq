"""Core protocol enums, bitflags, and action constants for QQ Official Bot v1/v2."""

from enum import IntEnum, IntFlag, StrEnum
from typing import Any

ADAPTER_NAME = "QQ"

T_JsonDict = dict[str, Any]

QQ_AUTH_URL = "https://bots.qq.com/app/getAppAccessToken"
QQ_API_BASE = "https://api.sgroup.qq.com"
QQ_SANDBOX_API_BASE = "https://sandbox.api.sgroup.qq.com"


class Intents(IntFlag):
    """QQ Official Gateway subscription intent bitmask."""

    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1
    GUILD_MESSAGES = 1 << 9
    GUILD_MESSAGE_REACTIONS = 1 << 10
    DIRECT_MESSAGE = 1 << 12
    OPEN_FORUMS_EVENT = 1 << 18
    AUDIO_OR_LIVE_CHANNEL_MEMBER = 1 << 19
    C2C_GROUP_AT_MESSAGES = 1 << 25
    INTERACTION = 1 << 26
    MESSAGE_AUDIT = 1 << 27
    FORUM_EVENT = 1 << 28
    AUDIO_ACTION = 1 << 29
    PUBLIC_GUILD_MESSAGES = 1 << 30


class OpCode(IntEnum):
    """QQ Gateway WebSocket and Webhook protocol OpCodes."""

    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    RESUME = 6
    RECONNECT = 7
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11
    WEBHOOK_VERIFY = 13


class MediaFileType(IntEnum):
    """QQ v2 rich-media file_type codes."""

    IMAGE = 1
    VIDEO = 2
    VOICE = 3
    FILE = 4


class QQMsgType(IntEnum):
    """QQ v2 Group/C2C message msg_type codes."""

    TEXT = 0
    MARKDOWN = 2
    ARK = 3
    EMBED = 4
    MEDIA = 7


class StreamState(IntEnum):
    """QQ v2 MessageStream state codes."""

    GENERATING = 1
    FINISHED = 10


class QQAction(StrEnum):
    """Declarative action identifiers routed through ActionDispatcher."""

    # Auth & Gateway
    GET_ACCESS_TOKEN = "get_access_token"  # noqa: S105
    ME = "me"
    URL_GET = "url_get"
    SHARD_URL_GET = "shard_url_get"
    PUT_INTERACTION = "put_interaction"

    # C2C & Group v2 Messaging
    POST_C2C_MESSAGES = "post_c2c_messages"
    DELETE_C2C_MESSAGE = "delete_c2c_message"
    POST_GROUP_MESSAGES = "post_group_messages"
    DELETE_GROUP_MESSAGE = "delete_group_message"
    SEND_GROUP_STREAM = "send_group_stream"
    SEND_C2C_STREAM = "send_c2c_stream"

    # Rich Media & BDH Chunked Upload
    POST_C2C_FILES = "post_c2c_files"
    POST_C2C_UPLOAD_PREPARE = "post_c2c_upload_prepare"
    POST_C2C_UPLOAD_PART = "post_c2c_upload_part"
    POST_C2C_UPLOAD_FINISH = "post_c2c_upload_finish"
    POST_GROUP_FILES = "post_group_files"
    POST_GROUP_UPLOAD_PREPARE = "post_group_upload_prepare"
    POST_GROUP_UPLOAD_PART = "post_group_upload_part"
    POST_GROUP_UPLOAD_FINISH = "post_group_upload_finish"
    DOWNLOAD_ATTACHMENT = "download_attachment"

    # Official Group Admin v2 (Full 11 endpoints + recall above)
    GET_GROUP_INFO = "get_group_info"
    GET_GROUP_BOT_STATE = "get_group_bot_state"
    GET_GROUP_MEMBERS = "get_group_members"
    POST_GROUP_MEMBERS = "post_group_members"
    GET_GROUP_MEMBER = "get_group_member"
    GET_GROUP_MUTE_SETTING = "get_group_mute_setting"
    SET_GROUP_MEMBERS_MUTE = "set_group_members_mute"
    GET_GROUP_JOIN_REQUEST_LIST = "get_group_join_request_list"
    APPROVAL_JOIN_REQUEST = "approval_join_request"
    BATCH_REMOVE_GROUP_MEMBERS = "batch_remove_group_members"
    GET_GROUP_MEMBER_BLACKLIST = "get_group_member_blacklist"
    POST_GROUP_MEMBER_BLACKLIST = "post_group_member_blacklist"

    # Guild Core v1
    GUILDS = "guilds"
    GET_GUILD = "get_guild"
    GET_CHANNELS = "get_channels"
    GET_CHANNEL = "get_channel"
    POST_CHANNELS = "post_channels"
    PATCH_CHANNEL = "patch_channel"
    DELETE_CHANNEL = "delete_channel"
    GET_MEMBERS = "get_members"
    GET_ROLE_MEMBERS = "get_role_members"
    GET_MEMBER = "get_member"
    DELETE_MEMBER = "delete_member"
    GET_GUILD_ROLES = "get_guild_roles"
    POST_GUILD_ROLE = "post_guild_role"
    PATCH_GUILD_ROLE = "patch_guild_role"
    DELETE_GUILD_ROLE = "delete_guild_role"
    PUT_GUILD_MEMBER_ROLE = "put_guild_member_role"
    DELETE_GUILD_MEMBER_ROLE = "delete_guild_member_role"
    GET_CHANNEL_PERMISSIONS = "get_channel_permissions"
    PUT_CHANNEL_PERMISSIONS = "put_channel_permissions"
    GET_CHANNEL_ROLES_PERMISSIONS = "get_channel_roles_permissions"
    PUT_CHANNEL_ROLES_PERMISSIONS = "put_channel_roles_permissions"

    # Guild Messaging & DMS v1
    GET_MESSAGE_OF_ID = "get_message_of_id"
    POST_MESSAGES = "post_messages"
    DELETE_MESSAGE = "delete_message"
    GET_MESSAGE_SETTING = "get_message_setting"
    POST_DMS = "post_dms"
    POST_DMS_MESSAGES = "post_dms_messages"
    DELETE_DMS_MESSAGE = "delete_dms_message"
    PUT_MESSAGE_REACTION = "put_message_reaction"
    DELETE_OWN_MESSAGE_REACTION = "delete_own_message_reaction"
    GET_REACTION_USERS = "get_reaction_users"
    PUT_PINS_MESSAGE = "put_pins_message"
    DELETE_PINS_MESSAGE = "delete_pins_message"
    GET_PINS_MESSAGE = "get_pins_message"
    POST_GUILD_ANNOUNCES = "post_guild_announces"
    DELETE_GUILD_ANNOUNCES = "delete_guild_announces"

    # Guild Extensions v1
    PATCH_GUILD_MUTE = "patch_guild_mute"
    PATCH_GUILD_MEMBER_MUTE = "patch_guild_member_mute"
    PATCH_GUILD_MUTE_MULTI_MEMBER = "patch_guild_mute_multi_member"
    GET_SCHEDULES = "get_schedules"
    GET_SCHEDULE = "get_schedule"
    POST_SCHEDULE = "post_schedule"
    PATCH_SCHEDULE = "patch_schedule"
    DELETE_SCHEDULE = "delete_schedule"
    AUDIO_CONTROL = "audio_control"
    PUT_MIC = "put_mic"
    DELETE_MIC = "delete_mic"
    GET_THREADS_LIST = "get_threads_list"
    GET_THREAD = "get_thread"
    PUT_THREAD = "put_thread"
    DELETE_THREAD = "delete_thread"
    GET_GUILD_API_PERMISSION = "get_guild_api_permission"
    POST_API_PERMISSION_DEMAND = "post_api_permission_demand"


__all__ = [
    "ADAPTER_NAME",
    "QQ_API_BASE",
    "QQ_AUTH_URL",
    "QQ_SANDBOX_API_BASE",
    "Intents",
    "MediaFileType",
    "OpCode",
    "QQAction",
    "QQMsgType",
    "StreamState",
    "T_JsonDict",
]
