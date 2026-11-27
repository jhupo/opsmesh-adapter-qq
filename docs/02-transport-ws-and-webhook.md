# 02. 双模入站传输协议设计（WebSocket 分片状态机 + Ed25519 Webhook）

本文档定义 `src/qq/transport/` 下 **WebSocket 客户端分片保活恢复** 与 **HTTP Webhook 验签回调** 两套入站接入机制的状态机与时序流程。

---

## 1. OpCode 协议帧定义

| OpCode | 名称 | 方向 | 作用 |
| :---: | :--- | :---: | :--- |
| `0` | `DISPATCH` | 服务端 -> 客户端 | 业务事件推送（携带序列号 `s` 与事件名 `t`） |
| `1` | `HEARTBEAT` | 双向 | 客户端定时发送最新 `s`；若收到服务端 `op=1` 立即回传一次心跳 |
| `2` | `IDENTIFY` | 客户端 -> 服务端 | 新连接鉴权、声明 `intents` 与 `shard: [id, count]` |
| `6` | `RESUME` | 客户端 -> 服务端 | 断线重连后携带 `session_id` 与 `last_seq` 请求补发离线事件 |
| `7` | `RECONNECT` | 服务端 -> 客户端 | 服务端通知客户端主动断开并立即执行 `RESUME` 重连 |
| `9` | `INVALID_SESSION` | 服务端 -> 客户端 | `IDENTIFY` 参数错误或 `RESUME` 会话过期，清空 `session_id` 重新鉴权 |
| `10` | `HELLO` | 服务端 -> 客户端 | WSS 建连首帧，下发 `heartbeat_interval`（毫秒） |
| `11` | `HEARTBEAT_ACK` | 服务端 -> 客户端 | 心跳确认帧（连续未收到触发断线重连） |
| `13` | `WEBHOOK_VERIFY` | 服务端 -> Webhook | HTTP 回调地址配置验证挑战帧 |

---

## 2. WebSocket 单分片连接状态机（`ws_session.py`）

多 Shard 场景下，同一个 `app_id` 只注册一个 `Gateway(id="qq:{app_id}")`：首个分片收到 `READY` 时调用 `gateway.connect()`，全部活跃分片均离线时调用 `gateway.disconnect()`。

```mermaid
stateDiagram-v2
    [*] --> Discovering: driver.on_startup
    Discovering --> Connecting: GET /gateway/bot 拿到 wss url 与分片数
    Discovering --> Backoff: 网络/鉴权异常

    Connecting --> AwaitHello: WSS 握手成功
    Connecting --> Backoff: WSS 握手失败

    AwaitHello --> Identifying: 收到 OP_HELLO(10) 且无 session_id
    AwaitHello --> Resuming: 收到 OP_HELLO(10) 且持有可恢复 session_id

    Identifying --> Online: 收到 READY · 记录 session_id & self_info · gateway.connect()
    Identifying --> InvalidSession: 收到 OP_INVALID_SESSION(9)

    Resuming --> Online: 收到 RESUMED · 补收离线帧完成
    Resuming --> InvalidSession: 收到 OP_INVALID_SESSION(9) · 清空 session_id

    InvalidSession --> Backoff: 等待退避后重新 Identify

    state Online {
        [*] --> Pumping
        Pumping --> Pumping: OP_DISPATCH(0) -> 更新 last_seq + 去重 + handle_event
        Pumping --> Pumping: 定时发送 OP_HEARTBEAT(1) -> 收到 OP_HEARTBEAT_ACK(11)
    }

    Online --> ReconnectNow: 收到 OP_RECONNECT(7) 或心跳超时 (保留 session_id)
    ReconnectNow --> Connecting: 0s~1s 快速重连走 Resuming

    Online --> Backoff: Socket 意外断开 (保留 session_id 优先尝试 Resume)
    Backoff --> Discovering: 指数退避 + 抖动等待结束

    Online --> Stopped: driver.on_shutdown (CancelScope) · gateway.disconnect()
    Stopped --> [*]
```

---

## 3. 时序图 1：WebSocket 鉴权、心跳与 `OP_RESUME` 断线补帧

```mermaid
sequenceDiagram
    autonumber
    participant SES as qq.transport.WSSession
    participant TOK as TokenManager
    participant API as api.sgroup.qq.com
    participant WSS as QQ WSS Gateway
    participant CORE as OpsMesh handle_event()

    SES->>TOK: get_token() -> POST bots.qq.com/app/getAppAccessToken
    TOK-->>SES: access_token
    SES->>API: GET /gateway/bot (Authorization: QQBot token)
    API-->>SES: {url: "wss://api.sgroup.qq.com/websocket", shards: 1}

    SES->>WSS: Connect WSS
    WSS->>SES: {op: 10, d: {heartbeat_interval: 41250}}
    SES->>WSS: {op: 2, d: {token: "QQBot ...", intents, shard: [0, 1]}}
    WSS->>SES: {op: 0, s: 1, t: "READY", d: {session_id: "sid_1", user: {id: "bot_u1", username: "OpsBot"}}}
    Note over SES: 保存 session_id="sid_1", last_seq=1 · 登记 gateway.connect()

    par 心跳保活协程
        loop 每 41.25 秒
            SES->>WSS: {op: 1, d: 1}
            WSS-->>SES: {op: 11}
        end
    and 事件消费协程
        WSS->>SES: {op: 0, s: 2, t: "GROUP_AT_MESSAGE_CREATE", d: {id: "msg_1", ...}}
        SES->>SES: last_seq=2 · DedupeRing("msg_1") · 登记被动回复窗口
        SES->>CORE: task_group.start_soon(handle_event, gateway, event)
    end

    WSS->>SES: {op: 7} (服务端平滑摘流通知重连)
    SES->>WSS: Close & Reconnect WSS
    WSS->>SES: {op: 10, d: {heartbeat_interval: 41250}}
    SES->>WSS: {op: 6, d: {token: "QQBot ...", session_id: "sid_1", seq: 2}}
    WSS-->>SES: {op: 0, s: 3, t: "GROUP_AT_MESSAGE_CREATE", d: {...}} (补推离线事件)
    WSS-->>SES: {op: 0, s: 4, t: "RESUMED", d: ""}
```

---

## 4. 时序图 2：HTTP Webhook `Ed25519` 挑战验证与事件验签（`webhook.py`）

当 `BotConfig.transport == "webhook"` 时，由 `app_secret` 循环填充至 32 字节作为种子派生 `Ed25519PrivateKey` 与对应公钥：

```mermaid
sequenceDiagram
    autonumber
    participant QQ as 腾讯 Webhook 推送端
    participant WH as qq.transport.WebhookHandler
    participant ED as Ed25519 Signer/Verifier
    participant CORE as OpsMesh handle_event()

    alt 阶段 A：开放平台配置回调地址验证 (op=13)
        QQ->>WH: POST /qq/webhook (Header: X-Bot-Appid, Body: {op: 13, d: {plain_token, event_ts}})
        WH->>ED: 使用 app_secret 派生私钥签名 (event_ts + plain_token)
        ED-->>WH: hex_signature
        WH-->>QQ: 200 OK {plain_token, signature: hex_signature}

    else 阶段 B：线上业务事件推送 (op=0)
        QQ->>WH: POST /qq/webhook (Headers: X-Bot-Appid, X-Signature-Ed25519, X-Signature-Timestamp)
        WH->>WH: 校验 Body <= 1 MiB 且定位对应 BotConfig
        WH->>ED:公钥验证 verify(signature, timestamp_bytes + raw_body_bytes)
        alt 签名无效或账号不存在
            WH-->>QQ: 403 Forbidden
        else 验签通过
            WH->>WH: DedupeRing 去重 + 解析 Event + 登记被动回复上下文
            WH->>CORE: task_group.start_soon(handle_event, gateway, event)
            WH-->>QQ: 200 OK (空响应体，毫秒级快速返回防平台重试)
        end
    end
```
