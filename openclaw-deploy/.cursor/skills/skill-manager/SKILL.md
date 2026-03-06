---
name: skill-manager
description: Manages OpenClaw agent native skills (command .md files) in config/commands/. Use when adding new agent commands, editing existing commands, listing available skills, creating slash commands for the agent, or managing what the agent can do natively.
---

# Skill Manager

管理 Agent 的原生技能（`config/commands/` 目录下的 `.md` 文件）。

## 技能文件位置

```
config/commands/
└── 美股行情.md    ← 已有：美股涨跌查询
```

Docker 容器内映射到：`/root/.openclaw/commands/`

## 技能文件格式

```markdown
---
description: 简短描述这个指令做什么
argument-hint: 参数提示（可选）
---

# 指令名称

指令的具体执行逻辑，告诉 Agent 如何响应这个命令。
使用什么工具、返回什么格式等。
```

## 现有技能

**美股行情**（`config/commands/美股行情.md`）
- 描述：查询美股涨跌行情
- 参数：条数（可选），如"美股行情 20"
- 工具：`get_market_movers`（us-market MCP）

## 添加新技能

1. 在 `config/commands/` 创建新 `.md` 文件
2. 按格式写好 frontmatter 和执行逻辑
3. 重新构建并部署

```bash
# 创建新技能后
make build && make up
```

## 技能示例模板

```markdown
---
description: 查询指定股票的实时行情和新闻
argument-hint: 股票代码，如"股票 NVDA"
---

# 股票详情

调用 `get_stock_quote` 获取 $ARGUMENTS 的实时行情。
再调用 `get_stock_news` 获取最新5条新闻并用中文简要说明。
以清晰的中文格式输出价格、涨跌、市值和关键新闻。
```

## 技能 vs Heartbeat vs Cron

| 场景 | 用技能 | 用 Heartbeat | 用 Cron |
|---|---|---|---|
| 用户主动触发 | ✅ | | |
| 后台定期执行 | | ✅ | ✅ |
| 需要精确时间 | | | ✅ |
