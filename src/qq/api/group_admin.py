"""Complete QQ Official Group Admin v2 APIs (all 11 group-admin endpoints)."""

from datetime import datetime, timedelta
from typing import Literal

from qq.config import BotConfig
from qq.event.models import (
    BatchRemoveMembersReturn,
    GroupBotStateReturn,
    GroupInfoReturn,
    GroupMemberBlacklistReturn,
    GroupMemberInfo,
    GroupMembersReturn,
    GroupRestrictChatSettingReturn,
    JoinRequestListReturn,
    MemberBlacklistOpReturn,
    PostGroupMembersReturn,
    SetMemberMuteState,
)
from qq.typing import T_JsonDict
from qq.utils import format_iso8601_utc, validate_qq_identifier

from .client import ApiClient
from .token import TokenManager


class GroupAdminService:
    """Full Tencent Official QQ Bot v2 Group Administration API service."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    async def get_group_info(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
    ) -> GroupInfoReturn:
        gid = validate_qq_identifier(group_openid, "group_openid")
        data = await self._client.request_json(
            "GET",
            f"/v2/groups/{gid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )
        return GroupInfoReturn.model_validate(data or {})

    async def get_group_bot_state(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
    ) -> GroupBotStateReturn:
        gid = validate_qq_identifier(group_openid, "group_openid")
        data = await self._client.request_json(
            "GET",
            f"/v2/groups/{gid}/bot",
            bot_config=bot_config,
            token_manager=token_manager,
        )
        return GroupBotStateReturn.model_validate(data or {})

    async def get_group_members(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> GroupMembersReturn:
        gid = validate_qq_identifier(group_openid, "group_openid")
        params: T_JsonDict = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        data = await self._client.request_json(
            "GET",
            f"/v2/groups/{gid}/members",
            bot_config=bot_config,
            token_manager=token_manager,
            params=params or None,
        )
        return GroupMembersReturn.model_validate(data or {})

    async def post_group_members(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
        limit: int | None = None,
        start_index: int | None = None,
    ) -> PostGroupMembersReturn:
        gid = validate_qq_identifier(group_openid, "group_openid")
        body: T_JsonDict = {}
        if limit is not None:
            body["limit"] = limit
        if start_index is not None:
            body["start_index"] = start_index
        data = await self._client.request_json(
            "POST",
            f"/v2/groups/{gid}/members",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=body,
        )
        return PostGroupMembersReturn.model_validate(data or {})

    async def get_group_member(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
        member_openid: str,
    ) -> GroupMemberInfo:
        gid = validate_qq_identifier(group_openid, "group_openid")
        mid = validate_qq_identifier(member_openid, "member_openid")
        data = await self._client.request_json(
            "GET",
            f"/v2/groups/{gid}/members/{mid}",
            bot_config=bot_config,
            token_manager=token_manager,
        )
        return GroupMemberInfo.model_validate(data or {})

    async def get_group_mute_setting(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
    ) -> GroupRestrictChatSettingReturn:
        gid = validate_qq_identifier(group_openid, "group_openid")
        data = await self._client.request_json(
            "GET",
            f"/v2/groups/{gid}/restrict_chat_setting",
            bot_config=bot_config,
            token_manager=token_manager,
        )
        return GroupRestrictChatSettingReturn.model_validate(data or {})

    async def set_group_members_mute(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
        members: list[SetMemberMuteState],
    ) -> None:
        gid = validate_qq_identifier(group_openid, "group_openid")
        serialized: list[T_JsonDict] = []
        for item in members:
            mid = validate_qq_identifier(item.member_openid, "member_openid")
            entry: T_JsonDict = {"member_openid": mid, "op": item.op}
            if item.mute_end_timestamp is not None:
                if isinstance(item.mute_end_timestamp, (datetime, timedelta)):
                    entry["mute_end_timestamp"] = format_iso8601_utc(
                        item.mute_end_timestamp
                    )
                else:
                    entry["mute_end_timestamp"] = item.mute_end_timestamp
            serialized.append(entry)

        await self._client.request_json(
            "POST",
            f"/v2/groups/{gid}/restrict_chat_setting",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body={"members": serialized},
        )

    async def get_group_join_request_list(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> JoinRequestListReturn:
        gid = validate_qq_identifier(group_openid, "group_openid")
        params: T_JsonDict = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        data = await self._client.request_json(
            "GET",
            f"/v2/groups/{gid}/join_request_list",
            bot_config=bot_config,
            token_manager=token_manager,
            params=params or None,
        )
        return JoinRequestListReturn.model_validate(data or {})

    async def approval_join_request(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
        member_openid: str,
        op: Literal["approve", "decline"],
        join_request_id: str | None = None,
        reject_reason: str | None = None,
        add_to_member_blacklist: bool | None = None,
    ) -> None:
        gid = validate_qq_identifier(group_openid, "group_openid")
        mid = validate_qq_identifier(member_openid, "member_openid")
        body: T_JsonDict = {"op": op}
        if join_request_id is not None:
            body["join_request_id"] = join_request_id
        if reject_reason is not None:
            body["reject_reason"] = reject_reason
        if add_to_member_blacklist is not None:
            body["add_to_member_blacklist"] = add_to_member_blacklist
        await self._client.request_json(
            "POST",
            f"/v2/groups/{gid}/approval_join_request/{mid}",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=body,
        )

    async def batch_remove_group_members(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
        member_openids: list[str],
        add_to_member_blacklist: bool | None = None,
    ) -> BatchRemoveMembersReturn:
        gid = validate_qq_identifier(group_openid, "group_openid")
        safe_mids = [validate_qq_identifier(m, "member_openid") for m in member_openids]
        body: T_JsonDict = {"member_openids": safe_mids}
        if add_to_member_blacklist is not None:
            body["add_to_member_blacklist"] = add_to_member_blacklist
        data = await self._client.request_json(
            "POST",
            f"/v2/groups/{gid}/batch_remove_members",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=body,
        )
        return BatchRemoveMembersReturn.model_validate(data or {})

    async def get_group_member_blacklist(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> GroupMemberBlacklistReturn:
        gid = validate_qq_identifier(group_openid, "group_openid")
        params: T_JsonDict = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        data = await self._client.request_json(
            "GET",
            f"/v2/groups/{gid}/member_blacklist",
            bot_config=bot_config,
            token_manager=token_manager,
            params=params or None,
        )
        return GroupMemberBlacklistReturn.model_validate(data or {})

    async def post_group_member_blacklist(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        group_openid: str,
        op: Literal["add", "del"],
        member_openids: list[str],
    ) -> MemberBlacklistOpReturn:
        gid = validate_qq_identifier(group_openid, "group_openid")
        safe_mids = [validate_qq_identifier(m, "member_openid") for m in member_openids]
        data = await self._client.request_json(
            "POST",
            f"/v2/groups/{gid}/member_blacklist",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body={"op": op, "member_openids": safe_mids},
        )
        return MemberBlacklistOpReturn.model_validate(data or {})


__all__ = ["GroupAdminService"]
