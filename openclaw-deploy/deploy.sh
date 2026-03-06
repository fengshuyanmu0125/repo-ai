#!/bin/bash
# OpenClaw 云服务器一键部署脚本
# 用法：bash deploy.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "========================================="
echo "  OpenClaw 云服务器一键部署"
echo "========================================="
echo ""

# ── 1. 检查 Docker ─────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "[1/4] Docker 未安装，正在安装..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
  echo "  Docker 安装完成"
else
  echo "[1/4] Docker 已安装: $(docker --version)"
fi

# 检查 docker compose
if ! docker compose version &>/dev/null; then
  echo "  安装 Docker Compose 插件..."
  apt-get update && apt-get install -y docker-compose-plugin
fi
echo "  Docker Compose: $(docker compose version --short 2>/dev/null || echo 'ready')"

# ── 2. 配置 .env ──────────────────────────────────────────────
if [ ! -f .env ]; then
  echo ""
  echo "[2/4] 创建 .env 配置文件..."
  cp .env.example .env

  # 自动生成 GATEWAY_TOKEN
  TOKEN=$(openssl rand -hex 24)
  sed -i "s/your_random_gateway_token_here/$TOKEN/" .env
  echo "  GATEWAY_TOKEN 已自动生成"

  echo ""
  echo "  ╔════════════════════════════════════════════╗"
  echo "  ║  请编辑 .env 文件填写 API 密钥:           ║"
  echo "  ║                                            ║"
  echo "  ║  vim $SCRIPT_DIR/.env                      ║"
  echo "  ║                                            ║"
  echo "  ║  必填项:                                   ║"
  echo "  ║  - ANTHROPIC_API_KEY  (Claude API 密钥)    ║"
  echo "  ║  - FEISHU_APP_ID     (飞书 App ID)        ║"
  echo "  ║  - FEISHU_APP_SECRET (飞书 App Secret)    ║"
  echo "  ║  - FEISHU_RECEIVE_ID (推送目标 ID)         ║"
  echo "  ║  - FINNHUB_API_KEY   (finnhub.io 免费)    ║"
  echo "  ╚════════════════════════════════════════════╝"
  echo ""
  echo "  填写完成后，重新运行: bash deploy.sh"
  exit 0
else
  echo "[2/4] .env 已存在，验证配置..."
  MISSING=0
  for KEY in ANTHROPIC_API_KEY FEISHU_APP_ID FEISHU_APP_SECRET FEISHU_RECEIVE_ID FINNHUB_API_KEY; do
    VAL=$(grep "^${KEY}=" .env | cut -d= -f2)
    if [ -z "$VAL" ] || echo "$VAL" | grep -q "xxxx"; then
      echo "  [!] $KEY 未配置"
      MISSING=1
    fi
  done
  if [ $MISSING -eq 1 ]; then
    echo ""
    echo "  请编辑 .env 填写以上缺失项后重新运行"
    exit 1
  fi
  echo "  所有必填项已配置"
fi

# ── 3. 构建并启动 ─────────────────────────────────────────────
echo ""
echo "[3/4] 构建并启动 Docker 容器..."
docker compose up -d --build

# ── 4. 验证 ───────────────────────────────────────────────────
echo ""
echo "[4/4] 验证服务状态..."
sleep 5
docker compose ps

echo ""
echo "========================================="
echo "  部署完成!"
echo "========================================="
echo ""
echo "  常用命令："
echo "    make logs         查看机器人日志"
echo "    make logs-report  查看日报日志"
echo "    make status       查看容器状态"
echo "    make restart      重启服务"
echo "    make run-report   手动触发日报"
echo "    make shell        进入容器 shell"
echo ""
echo "  飞书 Webhook 回调地址:"
echo "    http://<你的服务器IP>:18789"
echo ""
echo "  请确保云服务器防火墙已开放 18789 端口"
echo ""
