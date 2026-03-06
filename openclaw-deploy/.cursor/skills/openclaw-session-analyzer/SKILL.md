---
name: openclaw-session-analyzer
description: Analyzes OpenClaw agent session history and usage. Use when reviewing conversation history, checking token usage, analyzing what topics were discussed, inspecting session logs, or understanding agent activity patterns.
---

# OpenClaw Session Analyzer

分析 Agent 会话历史记录。

## 会话文件位置

Docker 容器内（通过 volume 持久化）：
```
/root/.openclaw/agents/main/sessions/
├── sessions.json      ← 会话索引
└── *.jsonl            ← 每个会话的消息记录
```

本地开发机：
```
~/.openclaw/agents/main/sessions/
```

## 查看会话

### 列出所有会话
```bash
# 本地
ls -lt ~/.openclaw/agents/main/sessions/*.jsonl | head -20

# Docker
docker compose exec openclaw ls -lt /root/.openclaw/agents/main/sessions/ | head -20
```

### 查看最新会话内容
```bash
# 本地（最新 .jsonl 文件）
tail -50 ~/.openclaw/agents/main/sessions/$(ls -t ~/.openclaw/agents/main/sessions/*.jsonl | head -1)
```

### 统计 Token 使用
```bash
# 统计所有会话的 token 字段
grep -h '"tokens"' ~/.openclaw/agents/main/sessions/*.jsonl | \
  python3 -c "
import sys, json
total_in = total_out = 0
for line in sys.stdin:
    try:
        d = json.loads(line.strip().rstrip(','))
        t = d.get('tokens', {})
        total_in += t.get('input', 0)
        total_out += t.get('output', 0)
    except: pass
print(f'Input: {total_in:,}  Output: {total_out:,}  Total: {total_in+total_out:,}')
"
```

## JSONL 格式说明

每行一个 JSON 对象：

```json
{"role": "user", "content": "...", "timestamp": "..."}
{"role": "assistant", "content": "...", "tokens": {"input": 1200, "output": 350}}
```

## 常用分析场景

**找某次对话**：按时间范围找 `.jsonl` 文件，文件名包含时间戳。

**检查 Agent 行为**：查看 `role: "tool"` 的记录，了解 Agent 调用了哪些工具。

**分析话题分布**：提取所有 `role: "user"` 的 content，让 AI 做主题归纳。
