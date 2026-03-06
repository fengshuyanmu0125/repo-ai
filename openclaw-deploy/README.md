# openclaw-deploy

自托管 OpenClaw AI Agent 部署套件，支持云服务器 Docker 一键部署。

## 结构

```
openclaw-deploy/
├── .env.example            所有密钥模板（复制后填写）
├── config/
│   ├── openclaw.tmpl.json  配置模板（env var 占位符）
│   ├── credentials/        飞书凭证
│   ├── identity/           设备身份
│   └── devices/            已配对设备
├── workspace/              Agent 大脑（挂载到宿主机）
│   ├── SOUL.md             Agent 人格
│   ├── IDENTITY.md         Agent 身份
│   ├── USER.md             用户信息
│   ├── HEARTBEAT.md        定期巡检任务
│   └── skills/finance/     /finance 行情查询 skill
├── plugins/us-market/      MCP 服务器（美股行情工具）
├── jobs/market-report/     定时日报任务
├── Dockerfile              主镜像
├── docker-entrypoint.sh    启动脚本（生成配置 + 启动 gateway）
├── docker-compose.yml      服务编排
└── Makefile                常用命令
```

## 云服务器快速部署

### 前置条件

- Docker + Docker Compose（`curl -fsSL https://get.docker.com | sh`）
- 飞书机器人已配置好 Webhook 事件订阅，回调地址指向服务器 `http://<IP>:18789`

### 步骤

```bash
# 1. 克隆项目
git clone <your-repo> openclaw-deploy && cd openclaw-deploy

# 2. 配置密钥
cp .env.example .env
vim .env   # 填写所有 API keys（见下方说明）

# 3. 一键部署
make deploy

# 4. 查看日志
make logs
```

### .env 配置说明

| 变量 | 说明 | 获取方式 |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API Key | [ai-nebula.com](https://ai-nebula.com) 或 Anthropic |
| `ANTHROPIC_BASE_URL` | API 代理地址 | 默认 `https://llm.ai-nebula.com` |
| `FEISHU_APP_ID` | 飞书机器人 App ID | 飞书开放平台 → 应用 |
| `FEISHU_APP_SECRET` | 飞书机器人 Secret | 飞书开放平台 → 应用 |
| `FEISHU_RECEIVE_ID` | 日报推送目标 ID | 飞书用户 open_id 或群 chat_id |
| `GATEWAY_TOKEN` | Gateway 鉴权 Token | `openssl rand -hex 24` |
| `FINNHUB_API_KEY` | Finnhub 数据 API Key | [finnhub.io](https://finnhub.io)（免费） |
| `TOP_N` | 日报显示股票数 | 默认 `10` |

### 飞书 Webhook 配置

在飞书开放平台 → 事件与回调 → 事件订阅，设置请求地址为：

```
http://<服务器公网IP>:18789
```

---

## 常用命令

```bash
make deploy       # 首次部署（检查 .env 并构建启动）
make up           # 启动
make down         # 停止
make restart      # 重启
make logs         # openclaw 实时日志
make logs-report  # 日报任务日志
make run-report   # 立即触发一次日报
make shell        # 进入 openclaw 容器
make status       # 查看容器状态
```

---

## 服务说明

### openclaw（主服务）
- 端口：`18789`（飞书 Webhook 回调 + Gateway API）
- 模型：Claude Sonnet 4.6（via ANTHROPIC_BASE_URL 代理）
- Channel：飞书（Feishu/Lark）
- MCP：`us-market`（美股行情工具集）
- Skill：`/finance`（按需查询单股/大盘/板块/加密）

### market-report（定时任务）
- 每日 01:00 UTC（北京时间 09:00）推送美股日报
- 仅工作日（周二至周六，覆盖周一至周五美股收盘）
- 数据：Yahoo Finance + Finnhub + Claude AI 分析

---

## 本地开发

```bash
# 本地启动（macOS）
openclaw gateway run

# 同步 skills 到本地
cp workspace/skills/finance/SKILL.md ~/.openclaw/workspace/skills/finance/SKILL.md

# 手动跑日报测试
cd jobs/market-report && python3 report.py
```
