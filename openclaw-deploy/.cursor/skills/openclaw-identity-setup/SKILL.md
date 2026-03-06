---
name: openclaw-identity-setup
description: Guides initialization of OpenClaw agent identity files (IDENTITY.md, USER.md). Use when bootstrapping a new agent, setting up agent personality, filling identity templates, or when IDENTITY.md / USER.md are empty.
---

# OpenClaw Agent Identity Setup

初始化 `workspace/` 中的 Agent 身份文件。

## 需要填写的文件

| 文件 | 内容 | 状态 |
|---|---|---|
| `workspace/IDENTITY.md` | Agent 名字、性格、风格 | ⚠️ 模板待填 |
| `workspace/USER.md` | 用户信息、偏好 | ⚠️ 模板待填 |
| `workspace/TOOLS.md` | 本地环境注释 | 已有基础内容 |
| `workspace/HEARTBEAT.md` | 定期巡检任务 | 空，按需填写 |

## 收集信息（先问用户）

**关于 Agent：**
- 叫什么名字？
- 性格风格？（幽默/严肃/随意/专业）
- 专长领域？（投资/编程/写作）
- 签名 emoji？

**关于用户：**
- 名字 / 怎么称呼？
- 职业 / 身份？
- 时区？
- 特别偏好或禁忌？

## IDENTITY.md 模板

```markdown
# IDENTITY.md

## 我是谁

**名字**: [Name]
**类型**: [AI助手/数字伙伴/...]
**Emoji**: [签名]

## 性格

[2-3 句话]

## 专长

- [专长 1]
- [专长 2]

## 说话风格

[简洁/详细/幽默...]
```

## USER.md 模板

```markdown
# USER.md

**姓名**: [Name]
**称呼**: [怎么叫]
**时区**: Asia/Shanghai
**职业**: [...]

## 偏好

- 喜欢: [...]
- 不喜欢: [...]

## 当前关注

[项目/话题/...]
```

## 完成后

```bash
# 重启 Agent 加载新身份
make restart

# 验证
make workspace
```
