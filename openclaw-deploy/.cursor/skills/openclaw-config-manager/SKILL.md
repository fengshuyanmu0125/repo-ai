---
name: openclaw-config-manager
description: Manages openclaw.json configuration for the deployed OpenClaw agent. Use when changing LLM model, adjusting concurrency, modifying channel settings, updating API keys, or configuring any openclaw.json settings.
---

# OpenClaw Config Manager

管理 `config/openclaw.json`（生产配置）。

## 配置文件位置

```
config/openclaw.json      ← 版本控制中的配置
```

Docker 启动时由 Dockerfile 复制到容器 `/root/.openclaw/openclaw.json`。

## 修改配置的安全流程

1. **备份** — 先备份当前配置
2. **编辑** — 修改 `config/openclaw.json`
3. **校验** — 运行 `make config-check`
4. **重建** — `make build && make up`

```bash
cp config/openclaw.json config/openclaw.json.bak
# ... 编辑 ...
make config-check
make build && make up
```

## 常用配置项速查

### 切换模型
```json
"agents": {
  "defaults": {
    "model": {
      "primary": "anthropic/claude-sonnet-4-6"
    }
  }
}
```

### 调整并发
```json
"agents": {
  "defaults": {
    "maxConcurrent": 4,
    "subagents": { "maxConcurrent": 8 }
  }
}
```

### 上下文压缩模式
```json
"compaction": { "mode": "safeguard" }
```
可选值：`safeguard`（默认保护）| `aggressive`（积极压缩）| `off`

### 添加新 LLM 供应商
```json
"models": {
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-...",
      "auth": "api-key",
      "models": [{ "id": "openai/gpt-4o", "api": "openai-chat" }]
    }
  }
}
```

### 更新 API Key
```json
"models": {
  "providers": {
    "anthropic": {
      "apiKey": "sk-new-key-here"
    }
  }
}
```

## ⚠️ 注意事项

- `config/credentials/` 已在 `.gitignore` 中，不要提交密钥
- 修改 `gateway.auth.token` 后需同步更新客户端配置
- `channels.feishu.accounts.main.appSecret` 属于高度敏感字段
