---
name: openclaw-memory-curator
description: Reviews and consolidates OpenClaw agent memory files. Use when organizing agent memory, compressing daily logs into long-term memory, cleaning up MEMORY.md, reviewing what the agent remembers, or maintaining workspace memory files.
---

# OpenClaw Memory Curator

整理和压缩 Agent 记忆文件。

## 记忆文件位置

```
workspace/
├── memory/
│   ├── YYYY-MM-DD.md       ← 每日原始日志（Agent 自动创建）
│   └── heartbeat-state.json
└── MEMORY.md               ← 长期精炼记忆（在 .gitignore 中）
```

## 记忆层级

| 文件 | 类型 | 保留时间 | 内容 |
|---|---|---|---|
| `memory/YYYY-MM-DD.md` | 原始日志 | 2-4 周 | 当日所有重要事件 |
| `MEMORY.md` | 精炼记忆 | 长期 | 提炼的关键信息 |

## 整理流程

### 1. 查看当前状态

```bash
ls workspace/memory/
cat workspace/MEMORY.md
```

### 2. 读取近期日志（让 Agent 执行）

让 Agent 读取最近 7-14 天的 `memory/*.md`，提取：
- 重要决策和原因
- 用户偏好和习惯
- 项目进展
- 值得记住的教训

### 3. 更新 MEMORY.md

MEMORY.md 的推荐结构：

```markdown
# MEMORY.md

_最后更新：YYYY-MM-DD_

## 用户偏好

- [提炼的偏好]

## 重要决策

- [决策 + 原因]

## 进行中的项目

- [项目名]: [状态]

## 教训 / 注意事项

- [值得记住的事]
```

### 4. 清理旧日志

```bash
# 删除 30 天前的日志（保留近期）
find workspace/memory/ -name "*.md" -mtime +30 -delete
```

## 注意

- `MEMORY.md` 和 `memory/` 在 `.gitignore` 中，不会提交
- 如需备份记忆，手动复制到安全位置
- Docker bind mount 确保记忆在容器重启后保留
