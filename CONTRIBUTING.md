# 贡献指南（Contributing）

## 开发环境准备

要求 **Python >= 3.11**：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "../OpsMesh[fastapi,httpx,websockets]" -e ".[dev]"
```

## 提交前验证

```bash
ruff check src tests examples
ruff format --check src tests examples
bandit -r src/qq -ll -ii
pytest -v
```

## 架构红线

1. **100% 复用 OpsMesh 核心原语**：所有事件、消息、网关调用、异常与日志均直接继承和使用 `opsmesh` 基类，严禁另建平行事件总线或裸 `requests` 同步调用。
2. **协议层与业务策略解耦**：本仓库仅提供无状态的 QQ 官方开放平台协议编解码、传输保活与 REST API 原子封装（含群管原子 API）；具体群管命令、词库、阶梯处罚与配额状态归属独立插件仓库 `opsmesh-plugin-qq-admin`。
3. **零硬编码路由墙**：所有出站动作统一由 `QQAction(StrEnum)` 与 `ActionDispatcher` 分发，`adapter.py` 不直接拼接任何腾讯接口 URL 或请求体字段。
