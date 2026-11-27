# 03. 消息模型、被动回复 `msg_seq` 治理、富媒体分片与流式输出设计

本文档定义 QQ 官方平台特有的 **OpenID 隔离体系**、**被动回复时效与 `msg_seq` 自动递增机制**、**`file_info` 富媒体与 BDH 大文件分片上传** 以及 **`MessageStream` 流式消息**。

---

## 1. OpenID 身份与会话隔离规则

腾讯官方 v2 协议不暴露数字 QQ 号与数字群号，所有标识均为当前 `AppID` 维度下的加密 OpenID：

| 场景 | 事件类 | `event.get_user_id()` | `event.get_session_id()` | `event.is_tome()` |
| :--- | :--- | :--- | :--- | :---: |
| QQ 单聊 | `C2CMessageCreateEvent` | `author.user_openid` | `f"c2c_{user_openid}"` | 恒为 `True` |
| QQ 群艾特消息 | `GroupAtMessageCreateEvent` | `author.member_openid` | `f"group_{group_openid}_{member_openid}"` | 恒为 `True` |
| QQ 群全量消息 | `GroupMessageCreateEvent` | `author.member_openid` | `f"group_{group_openid}_{member_openid}"` | 检查 `mentions` 含 `is_you` 或引用了本 Bot 消息 |
| 频道公域/全量消息 | `AtMessageCreateEvent` / `MessageCreateEvent` | `author.id` | `f"guild_{guild_id}_{channel_id}_{author.id}"` | `@` 事件恒为 `True`，全量消息检查 `@Bot` 或引用 |
| 频道私信 | `DirectMessageCreateEvent` | `author.id` | `f"dms_{guild_id}_{author.id}"` | 恒为 `True` |

> **入站文本净化**：群聊与子频道 `@Bot /cmd` 入站时，解析器自动剥离首部 `@Bot` 提及标签与紧随的前导空白，确保 OpsMesh `on_command("cmd", rule=to_me())` 在单聊、群聊、子频道中表现完全一致。

---

## 2. 被动回复 `PassiveReplyTracker` 与 `msg_seq` 自动递增流程

腾讯官方平台限制：**群聊被动回复有效期 5 分钟（最多回复 5 条），单聊被动回复有效期 60 分钟（最多回复 4 条）**，且针对同一 `msg_id` 多次发送时 `msg_seq` 必须严格递增，否则会被平台判定为重复请求吞没。

```mermaid
flowchart TD
    CALL["插件调用 matcher.send(msg) / gateway.send(event, msg)"] --> PARSE["拆分为有序发送批次 (文本/Markdown 批次 + 独立富媒体批次)"]
    PARSE --> LOOP["遍历每个待发批次"]
    LOOP --> TRACK{"检查 PassiveReplyTracker(event.id): 是否在有效期内且未超条数上限?"}

    TRACK -- "是 (走被动回复)" --> SEQ["在异步锁内原子递增 msg_seq (1 -> 2 -> 3...)"]
    SEQ --> ATTACH_ID["注入 msg_id = event.id, msg_seq = seq"]
    TRACK -- "否 (超时或超条数 -> 降级主动消息)" --> ACTIVE["不传 msg_id (消耗主动消息配额)"]

    ATTACH_ID --> MEDIA_CHK{"当前批次是否为本地图片/语音/视频/文件且无 file_info?"}
    ACTIVE --> MEDIA_CHK

    MEDIA_CHK -- "是" --> UP["先调 upload_media 换取 file_info -> 组装 msg_type=7"]
    MEDIA_CHK -- "否" --> DIRECT["组装 msg_type=0(文本) / 2(Markdown+Keyboard) / 3(Ark)"]

    UP --> POST["POST /v2/groups/{group_openid}/messages 或 /v2/users/{openid}/messages"]
    DIRECT --> POST
```

---

## 3. 时序图 3：富媒体单步上传与 BDH 大文件分片上传（`api/media.py`）

QQ 群聊与单聊发送图片（`1`）、视频（`2`）、语音 Silk（`3`）、文件（`4`）必须先换取 `file_info`：
- 小文件或公网 URL：直接调 `POST /v2/groups/{group_openid}/files`；
- 大文件本地字节流：走官方 **BDH 分片上传三步曲**（`prepare` 拿预签名分片 URL -> 并发 `PUT` 分片并计算 MD5 -> `part_finish` 合并换取 `file_info`，遇 `40093001` BDH 瞬态码自动重试一次）。

```mermaid
sequenceDiagram
    autonumber
    participant PLG as 业务插件
    participant GW as qq.Gateway
    participant MED as qq.api.MediaService
    participant API as api.sgroup.qq.com
    participant COS as 腾讯 COS 预签名节点

    PLG->>GW: send(event, MessageSegment.file(path="report.pdf"))
    GW->>MED: upload_group_file(group_openid, file_type=4, path="report.pdf")

    alt 小文件 (单步 Base64 上传) 或公网 URL
        MED->>API: POST /v2/groups/{group_openid}/files {file_type: 4, file_data / url, srv_send_msg: false}
        API-->>MED: {file_uuid, file_info, ttl}
    else 大文件 (BDH 分片直传)
        MED->>MED: 流式计算整文件 MD5 与 SHA1 及总字节数
        MED->>API: POST /v2/groups/{group_openid}/files/prepare {file_type: 4, file_name, file_size, md5, sha1}
        API-->>MED: {upload_id, block_size, parts: [{index, presigned_url}, ...], upload_config}
        loop 按 concurrency 并发上传各分片
            MED->>COS: PUT presigned_url (分片字节流)
            COS-->>MED: 200 OK
        end
        MED->>API: POST /v2/groups/{group_openid}/files/part_finish {upload_id, part_md5s}
        API-->>MED: {file_uuid, file_info, ttl}
    end

    MED-->>GW: 返回 file_info
    GW->>API: POST /v2/groups/{group_openid}/messages {msg_type: 7, media: {file_info}, msg_id, msg_seq}
    API-->>PLG: 返回 PostGroupMessagesReturn
```

---

## 4. 时序图 4：`MessageStream` 流式消息与 `InteractionCreate` 按钮回调

QQ 官方 v2 原生支持在群聊/单聊中进行大模型打字机流式回复（`MessageStream`）：首片传 `state=1, index=1` 拿到流式会话 `id`，后续分片递增 `index` 并携带该 `id`，结束片传 `state=10` 固化消息。

```mermaid
sequenceDiagram
    autonumber
    participant PLG as 业务插件 (LLM)
    participant STR as gateway.message_stream(event)
    participant API as api.sgroup.qq.com
    participant USR as QQ 客户端用户

    PLG->>STR: async with gateway.message_stream(event) as stream
    PLG->>STR: await stream.append("第一段内容...")
    STR->>API: POST /v2/groups/{id}/messages {msg_type: 2, markdown: {...}, stream: {state: 1, index: 1}, msg_id, msg_seq}
    API-->>STR: {id: "stream_msg_01"} (锁定流式消息 ID)
    API-->>USR: 展示流式生成中气泡

    loop 后续节流分片
        PLG->>STR: await stream.append("后续内容...")
        STR->>API: POST /v2/groups/{id}/messages {msg_type: 2, markdown: {...}, stream: {state: 1, id: "stream_msg_01", index: N}, msg_id, msg_seq}
        API-->>USR: 原地刷新气泡文本
    end

    STR->>API: POST /v2/groups/{id}/messages {msg_type: 2, markdown: {...}, stream: {state: 10, id: "stream_msg_01", index: N+1}, msg_id, msg_seq}
    API-->>USR: 结束生成态（可附带 MessageActionButton / Keyboard 交互按钮）

    opt 用户点击消息下方的交互按钮
        USR->>API: 点击 Keyboard 按钮 (callback_data="approve:req_1")
        API->>PLG: 推送 INTERACTION_CREATE -> InteractionCreateEvent
        PLG->>API: gateway.put_interaction(interaction_id=event.id, code=0) (确认按钮交互成功)
    end
```
