---
name: heartbeat-manager
description: Configures and manages the OpenClaw agent heartbeat task list in HEARTBEAT.md. Use when setting up periodic checks, adding proactive monitoring tasks, configuring what the agent should do automatically, or managing background agent behavior.
---

# Heartbeat Manager

管理 `workspace/HEARTBEAT.md`，定义 Agent 的定期巡检任务。

## 什么是心跳

Agent 定期（约每 30 分钟）收到心跳触发，读取 `HEARTBEAT.md` 并执行其中的任务。文件为空时直接回复 `HEARTBEAT_OK`。

## 文件位置

```
workspace/HEARTBEAT.md
```

## 格式规范

```markdown
# HEARTBEAT.md

- [ ] 检查任务 1
- [ ] 检查任务 2
```

**关键原则**：
- 保持 < 30 行（减少 token 消耗）
- 用 `[ ]` checkbox 格式
- 每条任务要具体、可操作

## 常用任务模板

```markdown
# HEARTBEAT.md

- [ ] 检查是否有重要飞书消息未回复
- [ ] 查看美股市场有无异常波动（用 get_market_movers）
- [ ] 确认 market-report 容器今日是否正常运行
- [ ] 如距上次问候超过 8 小时且非深夜，主动打个招呼
```

## 心跳 vs Cron 选择

| 场景 | 用心跳 | 用 Cron |
|---|---|---|
| 多个检查可以合并 | ✅ | |
| 时间可以有偏差（±30min） | ✅ | |
| 需要精确时间（9:00 整） | | ✅ |
| 任务需要独立会话 | | ✅ |
| 直接推送到 channel | | ✅ |

## 修改后生效

心跳任务修改后**无需重启**，Agent 下次心跳时自动读取新内容。

```bash
# 查看当前心跳配置
cat workspace/HEARTBEAT.md

# 如使用 Docker，进入容器查看实时状态
make workspace-shell
```
