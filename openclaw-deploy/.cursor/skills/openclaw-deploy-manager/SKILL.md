---
name: openclaw-deploy-manager
description: Manages deployment operations for the openclaw-deploy project. Use when deploying to server, rebuilding Docker containers, updating openclaw version, managing environment variables, troubleshooting deployment issues, or running make commands.
---

# OpenClaw Deploy Manager

管理 `~/ai/openclaw-deploy` 的部署操作。

## 常用操作速查

```bash
make up           # 启动所有服务
make down         # 停止所有服务
make restart      # 重启 openclaw 主服务
make build        # 重新构建镜像（不缓存）
make logs         # 查看 openclaw 日志
make logs-report  # 查看 market-report 日志
make ps           # 查看容器状态
make workspace    # 查看 Agent workspace 状态
make run-report   # 手动触发美股日报
make config-check # 验证 openclaw.json 格式
```

## 首次部署流程

```bash
# 1. 准备环境变量
cp .env.example .env
# 编辑 .env 填写真实密钥

# 2. 初始化 Agent 身份（重要！）
# 编辑 workspace/IDENTITY.md 和 workspace/USER.md

# 3. 部署
make deploy        # Docker 模式
# 或
make deploy-native # 裸机模式

# 4. 验证
make ps
make logs
```

## 更新 openclaw 版本

```bash
# 重新构建镜像（会拉取最新 npm 包）
make build
make up
```

## 服务说明

| 服务 | 描述 | 端口 |
|---|---|---|
| `openclaw` | 主 Agent 网关 | 18789 |
| `market-report` | 美股日报（定时触发）| — |

## 排查问题

```bash
# 查看完整日志
make logs

# 进入容器调试
docker compose exec openclaw bash

# 检查配置
make config-check

# 检查容器内 workspace
make workspace-shell
```

## Docker Volumes

| 名称 | 路径 | 类型 |
|---|---|---|
| `./workspace` | `/root/.openclaw/workspace` | bind mount（版本控制） |
| `openclaw_logs` | `/root/.openclaw/logs` | named volume |
