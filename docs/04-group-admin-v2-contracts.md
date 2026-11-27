# 04. QQ 官方群管理 API v2 全量契约与权限原语设计

本文档定义 `src/qq/api/group_admin.py`、`src/qq/event/group_notice.py` 与 `src/qq/permission.py` 完整覆盖的腾讯官方 QQ 群聊管理 v2 协议契约。

---

## 1. 官方群管前置条件与 OpenID 约束

1. **机器人群内身份要求**：目标群聊必须已添加该机器人，且调用禁言、踢人、黑名单、入群审批接口时，**机器人在该群内的 `member_role` 必须为 `"admin"`（管理员）或 `"owner"`（群主）**（可通过 `get_group_bot_state` 查询）。
2. **开放平台权限开通**：需在 QQ 开放平台后台为应用勾选群管理、群成员管理与对应 `GROUP_*` 事件订阅权限。
3. **安全路径校验**：所有传入 URL 路径的 `group_openid` 与 `member_openid` 均经 `validate_qq_identifier()` 严格校验（非空、长度 ≤ 256、禁止 `/`、`..`、空白与控制字符）。

---

## 2. 群管理 API v2 全量 11 项接口契约表（`api/group_admin.py`）

加上 `messaging.py` 中的群消息撤回 `delete_group_message`，共 **12 项群管原子动作**，100% 覆盖 `nonebot/adapter-qq` 上游能力：

| `Gateway` 方法 / `QQAction` | HTTP 方法与路径 | 核心入参 | 返回模型 |
| :--- | :--- | :--- | :--- |
| `get_group_info` | `GET /v2/groups/{group_openid}` | `group_openid` | `GroupInfoReturn`（群名、人数、简介、标签） |
| `get_group_bot_state` | `GET /v2/groups/{group_openid}/bot` | `group_openid` | `GroupBotStateReturn`（`member_role`、`allow_proactive_msg`、`recv_msg_setting`） |
| `get_group_members` | `GET /v2/groups/{group_openid}/members` | `group_openid, cursor=None` | `GroupMembersReturn`（成员列表含 `username`、`member_role`、`joined_at`、`bot`） |
| `post_group_members` | `POST /v2/groups/{group_openid}/members` | `group_openid, limit=..., start_index=...` | `PostGroupMembersReturn`（兼容索引分页查询） |
| `get_group_member` | `GET /v2/groups/{group_openid}/members/{member_openid}` | `group_openid, member_openid` | `GroupMemberInfo`（单个成员角色与资料） |
| `get_group_mute_setting` | `GET /v2/groups/{group_openid}/restrict_chat_setting` | `group_openid` | `GroupRestrictChatSettingReturn`（全体禁言规则 + 被禁言成员列表） |
| `set_group_members_mute` | `POST /v2/groups/{group_openid}/restrict_chat_setting` | `group_openid, members: list[SetMemberMuteState]` | `None`（支持 `op="add"\|"update"\|"del"`，自动将 `timedelta`/`datetime` 转为带时区 ISO8601） |
| `get_group_join_request_list` | `GET /v2/groups/{group_openid}/join_request_list` | `group_openid, cursor=None, limit=None` | `JoinRequestListReturn`（待处理入群申请单与问答信息） |
| `approval_join_request` | `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}` | `group_openid, member_openid, op="approve"\|"decline", join_request_id=..., reject_reason=..., add_to_member_blacklist=...` | `None` |
| `batch_remove_group_members` | `POST /v2/groups/{group_openid}/batch_remove_members` | `group_openid, member_openids: list[str], add_to_member_blacklist=None` | `BatchRemoveMembersReturn`（踢出结果与拉黑失败列表） |
| `get_group_member_blacklist` | `GET /v2/groups/{group_openid}/member_blacklist` | `group_openid, cursor=None, limit=None` | `GroupMemberBlacklistReturn`（黑名单成员与拉黑时间） |
| `post_group_member_blacklist` | `POST /v2/groups/{group_openid}/member_blacklist` | `group_openid, op="add"\|"del", member_openids: list[str]` | `MemberBlacklistOpReturn` |
| `delete_group_message` | `DELETE /v2/groups/{group_openid}/messages/{message_id}` | `group_openid, message_id` | `None`（撤回 2 分钟内消息） |

---

## 3. 入站群通知事件契约（`event/group_notice.py`）

全部继承 `NoticeEvent`（`get_type() -> "notice"`），可直接通过 `on_type(...)` 或 `on_notice()` 订阅：

| 官方事件名 (`t`) | 事件类 | 关键字段 |
| :--- | :--- | :--- |
| `GROUP_JOIN_REQUEST` | `GroupJoinRequestEvent` | `group_openid`, `join_request_id`, `member_openid`, `username`, `apply_source`, `invited_by`, `verify_info`, `risk_tips`, `auto_approved` |
| `GROUP_MEMBER_ADD` | `GroupMemberAddEvent` | `group_openid`, `member_openid`, `timestamp` |
| `GROUP_MEMBER_REMOVE` | `GroupMemberRemoveEvent` | `group_openid`, `member_openid`, `timestamp` |
| `GROUP_ADD_ROBOT` | `GroupAddRobotEvent` | `group_openid`, `op_member_openid`, `timestamp` |
| `GROUP_DEL_ROBOT` | `GroupDelRobotEvent` | `group_openid`, `op_member_openid`, `timestamp` |
| `GROUP_MSG_RECEIVE` | `GroupMsgReceiveEvent` | 群管理员开启接收机器人主动消息通知 |
| `GROUP_MSG_REJECT` | `GroupMsgRejectEvent` | 群管理员关闭接收机器人主动消息通知 |

---

## 4. 零开销群角色权限原语（`src/qq/permission.py`）

QQ 群消息事件 `GroupAtMessageCreateEvent` / `GroupMessageCreateEvent` 的 `author` 对象自带 `member_role: Literal["member", "admin", "owner"]`。适配器据此内置 4 个零网络开销的 `opsmesh.permission.Permission` 实例：

- **`GROUP_OWNER`**：仅匹配群主（`event.author.member_role == "owner"`）
- **`GROUP_ADMIN`**：仅匹配群管理员（`event.author.member_role == "admin"`）
- **`GUILD_OWNER`**：仅匹配频道主
- **`GUILD_ADMIN`**：仅匹配频道管理员

上层群管插件只需声明 `permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN`，即可在进入业务处理器之前完成毫秒级零 API 鉴权。
