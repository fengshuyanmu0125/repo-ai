# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

### exec 工具

本地 gateway 支持 `exec` 工具，可以执行 shell 命令。用法：
- tool: `exec`
- host: `gateway`
- command: 要执行的命令

示例：
```
exec(host="gateway", command="python3 /root/.openclaw/plugins/stock-query/query.py NVDA")
```

### /finance 行情查询

用户发 `/finance NVDA` 时，使用 exec 工具执行：
```
python3 /root/.openclaw/plugins/stock-query/query.py NVDA
```

脚本会输出飞书卡片 JSON，然后用 feishu_chat 的 send_interactive_message 发送。

---

Add whatever helps you do your job. This is your cheat sheet.
