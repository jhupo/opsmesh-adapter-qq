# 04. QQ 官方群管理 API v2 全量契约与权限原语设计

本文档定义 `src/qq/api/group_admin.py`、`src/qq/event/group_notice.py` 与 `src/qq/permission.py` 完整覆盖的腾讯官方 QQ 群聊管理 v2 协议契约。

---

## 1. 官方群管前置条件与 OpenID 约束

1. **机器人群内身份要求**：调用禁言、踢人、黑名单、入群审批与消息撤回接口时，**机器人在该群内的 `member_role` 必须为 `"admin"`（管理员）或 `"owner"`（群主）**（可通过 `get_group_bot_state` 查询）。
2. **安全路径校验**：所有传入 URL 路径的 `group_openid` 与 `member_openid` 均经 `validate_qq_identifier()` 严格校验。
3. **上层面向对象封装边界**：适配器仅做 1:1 官方协议映射；单群作用域绑定、时长字符串解析、游标自动翻页与 OpsMesh `Depends` 注入由独立库插件 **[opsmesh-plugin-qq-admin](https://github.com/jhupo/opsmesh-plugin-qq-admin)**（`QQGroupAdmin` / `QQGroupScope`）提供。

---

## 2. 群管理 API v2 全量 12 项接口契约表

| `Gateway` 方法 / `QQAction` | HTTP 方法与路径 | 核心入参 | 返回模型 |
| :--- | :--- | :--- | :--- |
| `get_group_info` | `GET /v2/groups/{gid}/info` | `group_openid` | `GroupInfoReturn`（`group_name`、`group_member_num`、`group_finger_memo`、`group_class_text`、`group_tags`） |
| `get_group_bot_state` | `GET /v2/groups/{gid}/bot_state` | `group_openid` | `GroupBotStateReturn`（`member_role`、`allow_proactive_msg`、`recv_msg_setting`、`joined_at`） |
| `get_group_members` | `GET /v2/groups/{gid}/members` | `group_openid, cursor=None, limit=None` | `GroupMembersReturn`（`members: list[GroupMemberInfo]`、`next_cursor`） |
| `post_group_members` | `POST /v2/groups/{gid}/members` | `group_openid, limit=..., start_index=...` | `PostGroupMembersReturn`（`members: list[GroupMember]`、`next_index`） |
| `get_group_member` | `GET /v2/groups/{gid}/members/{mid}` | `group_openid, member_openid` | `GroupMemberInfo`（单个成员角色与资料） |
| `get_group_mute_setting` | `GET /v2/groups/{gid}/restrict_chat_setting` | `group_openid` | `GroupRestrictChatSettingReturn`（`global_rule` + `members: list[MemberMuteState]`） |
| `set_group_members_mute` | `POST /v2/groups/{gid}/restrict_chat_setting` | `group_openid, members: list[SetMemberMuteState]` | `None`（`op="add"\|"update"\|"del"`，`mute_expire_at` 自动转为带时区 ISO8601） |
| `get_group_join_request_list` | `GET /v2/groups/{gid}/join_request_list` | `group_openid, cursor=None, limit=None` | `JoinRequestListReturn`（`list: list[JoinRequest]`、`next_cursor`） |
| `approval_join_request` | `POST /v2/groups/{gid}/approval_join_request/{mid}` | `group_openid, member_openid, op="approve"\|"decline", join_request_id=..., reject_reason=..., add_to_member_blacklist=...` | `None` |
| `batch_remove_group_members` | `POST /v2/groups/{gid}/batch_remove_members` | `group_openid, member_openids: list[str], add_to_member_blacklist=None` | `BatchRemoveMembersReturn`（`remove_members_result`、`add_to_member_blacklist_fail_openids`） |
| `get_group_member_blacklist` | `GET /v2/groups/{gid}/member_blacklist` | `group_openid, cursor=None, limit=None` | `GroupMemberBlacklistReturn`（`users: list[BlacklistUser]`、`next_cursor`） |
| `post_group_member_blacklist` | `POST /v2/groups/{gid}/member_blacklist` | `group_openid, op="add"\|"del", member_openids: list[str]` | `MemberBlacklistOpReturn`（`fail_openids`） |
| `delete_group_message` | `DELETE /v2/groups/{gid}/messages/{msg_id}` | `group_openid, message_id` | `None`（撤回 2 分钟内消息） |

---

## 3. 零开销群角色权限原语（`src/qq/permission.py`）

- **`GROUP_OWNER`**：仅匹配群主（`event.author.member_role == "owner"`）
- **`GROUP_ADMIN`**：仅匹配群管理员（`event.author.member_role == "admin"`）
- **`GUILD_OWNER`** / **`GUILD_ADMIN`**：匹配频道主与频道管理员
