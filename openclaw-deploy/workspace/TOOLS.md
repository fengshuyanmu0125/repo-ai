# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff unique to this deployment.

## MCP Servers

### us-market
- Path: `/root/.openclaw/plugins/us-market/server.py`
- Tools: `get_market_movers`, `get_stock_quote`, `get_stock_news`
- Data source: Yahoo Finance (no API key needed)

## Feishu

- App ID: see `openclaw.json`
- Channel: `main`
- DM policy: allowlist (check `credentials/feishu-main-allowFrom.json`)

## Commands (Native Skills)

- `美股行情` — 查询 S&P 100 涨跌榜（调用 us-market MCP）

## Environment

_(Add deployment-specific notes here: server IP, container names, cron schedules, etc.)_

---

Add whatever helps you do your job. This is your cheat sheet.
