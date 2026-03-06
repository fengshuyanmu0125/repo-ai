---
name: mcp-server-manager
description: Manages MCP (Model Context Protocol) servers for the OpenClaw agent. Use when adding new MCP tools, configuring MCP servers, troubleshooting MCP connections, extending agent capabilities with external APIs, or managing the us-market plugin.
---

# MCP Server Manager

管理 Agent 的 MCP 工具服务器。

## 现有 MCP 服务器

### us-market（已配置）
- 文件：`plugins/us-market/server.py`
- 容器路径：`/root/.openclaw/plugins/us-market/server.py`
- 工具：
  - `get_market_movers(top_n)` — S&P 100 涨跌榜
  - `get_stock_quote(symbol)` — 单股行情
  - `get_stock_news(symbol, max_items)` — 股票新闻

## MCP 配置位置

`config/openclaw.json` 中：

```json
"mcp": {
  "servers": {
    "us-market": {
      "command": "python3",
      "args": ["/root/.openclaw/plugins/us-market/server.py"]
    }
  }
}
```

## 添加新 MCP 服务器

### 步骤

1. 在 `plugins/` 下创建新目录和服务器文件
2. 在 `config/openclaw.json` 的 `mcp.servers` 中注册
3. 如有 Python 依赖，在 `Dockerfile` 中添加 pip install
4. 重新构建部署

### 示例：添加天气 MCP

```python
# plugins/weather/server.py
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("weather")

@mcp.tool()
def get_weather(city: str) -> str:
    """获取指定城市的天气"""
    # ...实现...

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

```json
// config/openclaw.json
"mcp": {
  "servers": {
    "us-market": { ... },
    "weather": {
      "command": "python3",
      "args": ["/root/.openclaw/plugins/weather/server.py"]
    }
  }
}
```

```dockerfile
# Dockerfile 新增依赖
RUN pip3 install --no-cache-dir --break-system-packages \
    requests
```

```bash
# 重新构建
make build && make up
```

## MCP 开发规范

- 用 `FastMCP` 框架（项目已使用）
- 每个工具必须有 docstring（Agent 读取来理解用途）
- transport 固定用 `stdio`
- 错误要 return 字符串，不要 raise（避免 Agent 崩溃）

## 调试 MCP

```bash
# 本地测试 MCP server
python3 plugins/us-market/server.py

# 容器内查看 MCP 日志
make logs
```

## 常用 MCP 扩展想法

| 用途 | 数据源 |
|---|---|
| A 股行情 | 新浪财经 / 东方财富 |
| 日历查询 | Google Calendar API |
| 邮件摘要 | Gmail API |
| 网页搜索 | Tavily / Serper |
| 加密货币 | CoinGecko |
