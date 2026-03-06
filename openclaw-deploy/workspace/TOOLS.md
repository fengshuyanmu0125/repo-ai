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

### /finance 行情查询

用户发 `/finance NVDA` 或 `/finance market` 时：**必须用 exec 工具**在 gateway 上执行 Python（本机已装 yfinance），**禁止**使用网页搜索、Brave API 或任何联网查行情。直接运行 skill 里给出的 Python 脚本即可。

---

Add whatever helps you do your job. This is your cheat sheet.
