#!/bin/bash
# openclaw-cn 云服务器部署脚本
# 用法：
#   bash setup.sh          # 直接安装（不用 Docker）
#   bash setup.sh --docker  # 用 Docker 运行

set -e

MODE="native"
[[ "$1" == "--docker" ]] && MODE="docker"

echo "=== openclaw-cn 部署 (mode: $MODE) ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/config"

if [[ "$MODE" == "docker" ]]; then
  # ── Docker 模式 ────────────────────────────────────────────────────────────
  if ! command -v docker &>/dev/null; then
    echo "安装 Docker..."
    curl -fsSL https://get.docker.com | sh
  fi

  echo "构建并启动容器..."
  cd "$SCRIPT_DIR"
  docker compose up -d --build

  echo ""
  echo "✓ 已启动。查看日志："
  echo "  docker compose logs -f"
  echo "  docker compose down   # 停止"

else
  # ── 原生模式 ───────────────────────────────────────────────────────────────
  if ! command -v node &>/dev/null; then
    echo "[1/4] 安装 Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
  else
    echo "[1/4] Node.js 已安装: $(node -v)"
  fi

  echo "[2/4] 安装 openclaw-cn..."
  npm install -g openclaw-cn

  echo "[3/4] 写入配置..."
  OPENCLAW_DIR="$HOME/.openclaw"
  mkdir -p "$OPENCLAW_DIR"/{credentials,identity,devices,workspace/memory}

  cp "$CONFIG_DIR/openclaw.json"                          "$OPENCLAW_DIR/openclaw.json"
  cp "$CONFIG_DIR/credentials/feishu-main-allowFrom.json" "$OPENCLAW_DIR/credentials/"
  cp "$CONFIG_DIR/credentials/feishu-pairing.json"        "$OPENCLAW_DIR/credentials/"
  cp "$CONFIG_DIR/identity/device.json"                   "$OPENCLAW_DIR/identity/"
  cp "$CONFIG_DIR/identity/device-auth.json"              "$OPENCLAW_DIR/identity/"
  cp "$CONFIG_DIR/devices/paired.json"                    "$OPENCLAW_DIR/devices/"
  cp "$CONFIG_DIR/devices/pending.json"                   "$OPENCLAW_DIR/devices/"

  # 写入 Agent workspace（仅复制不存在的文件，不覆盖已初始化的身份）
  for f in "$SCRIPT_DIR/workspace/"*.md; do
    fname=$(basename "$f")
    if [ ! -f "$OPENCLAW_DIR/workspace/$fname" ]; then
      cp "$f" "$OPENCLAW_DIR/workspace/"
    fi
  done

  echo "[4/4] 完成！"
  echo ""
  echo "启动命令："
  echo "  openclaw-cn gateway start --foreground   # 前台运行"
  echo "  nohup openclaw-cn gateway start &        # 后台运行"
fi
