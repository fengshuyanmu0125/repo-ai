---
name: openclaw-cron-scheduler
description: Manages OpenClaw cron jobs for scheduled tasks. Use when creating scheduled tasks, setting up recurring jobs, configuring exact-time triggers, managing cron job JSON, or asking about automating periodic reports or reminders.
---

# OpenClaw Cron Scheduler

管理定时任务（精确时间触发的任务）。

## Cron Jobs 文件

Docker 容器内路径：`/root/.openclaw/cron/jobs.json`

如需版本控制，在本项目添加：
```
config/cron/jobs.json   ← 并在 Dockerfile 中 COPY
```

## Job 结构

```json
{
  "jobs": [
    {
      "id": "morning-brief",
      "name": "早间简报",
      "schedule": "0 9 * * 1-5",
      "prompt": "查看今日日历和邮件，用中文发送早间简报到飞书",
      "model": "anthropic/claude-sonnet-4-6",
      "enabled": true
    }
  ]
}
```

## 字段说明

| 字段 | 说明 |
|---|---|
| `id` | 唯一标识，小写+连字符 |
| `schedule` | Cron 表达式（5段）|
| `prompt` | 执行时发给 Agent 的指令 |
| `model` | 使用的模型（可选，默认用主模型）|
| `enabled` | 是否启用 |

## 常用 Cron 表达式

```
0 9 * * 1-5      每周一到五 9:00
0 22 * * *       每天 22:00
0 9,21 * * *     每天 9:00 和 21:00
*/30 * * * *     每 30 分钟
0 10 * * 1       每周一 10:00
```

## 当前已有定时任务

`market-report` 是通过 Docker 服务（独立容器）实现的，不是 OpenClaw cron：

```yaml
# docker-compose.yml
market-report:
  build: ./jobs/market-report
  restart: unless-stopped
```

如要改为 OpenClaw cron 管理，将 `report.py` 的逻辑转为 prompt 形式。

## 添加新 Cron Job

```bash
# 1. 编辑/创建 cron jobs 文件
# 2. 如使用 Docker，重启让容器加载
make restart
```
