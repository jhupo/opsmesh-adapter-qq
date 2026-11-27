# 安全策略（Security Policy）

## 安全设计基线

- **凭证掩码保护**：`app_secret` 统一使用 `pydantic.SecretStr` 存储，禁止出现在日志或异常文本中。
- **Webhook 强制验签**：HTTP Webhook 回调模式强制使用 `Ed25519` 校验 `X-Signature-Ed25519` 与 `X-Signature-Timestamp`，并限制单次请求体上限（1 MiB）。
- **媒体下载防 SSRF**：入站附件拉取强制校验 `https` 与腾讯官方媒体域名白名单，流式限额读取。
- **OpenID 路径注入防护**：拼接到 REST URL 路径中的 `group_openid`、`member_openid`、`channel_id` 等标识符均经过字符集与长度校验，阻断路径穿越（`..` / `/`）。

## 漏洞上报

请通过 GitHub Security Advisories 私密上报潜在安全问题。
