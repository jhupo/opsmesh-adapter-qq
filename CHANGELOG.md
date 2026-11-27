# 变更日志（Changelog）

本文件遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范，版本号遵循 [语义化版本（Semantic Versioning）](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added
- 初始化 `opsmesh-adapter-qq` 项目骨架（顶层包名 `qq`）与跨平台 CI / CodeQL / 安全扫描流水线。
- 完成对标 `nonebot/adapter-qq` 全量 API（C2C、群聊、v2 群管理 11 项接口、富媒体分片上传、流式消息、频道 v1、WebSocket 分片恢复与 Ed25519 Webhook）的四层模块化架构与时序设计文档。
