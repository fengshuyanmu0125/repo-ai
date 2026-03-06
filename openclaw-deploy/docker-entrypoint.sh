#!/bin/sh
set -e

OPENCLAW_DIR="/root/.openclaw"
CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"
TMPL_FILE="$OPENCLAW_DIR/openclaw.tmpl.json"

# ── 1. 从模板生成 openclaw.json（env var 替换）─────────────────
echo "[entrypoint] 生成 openclaw.json ..."
if [ -f "$TMPL_FILE" ]; then
  envsubst < "$TMPL_FILE" > "$CONFIG_FILE"
  echo "[entrypoint] openclaw.json 已生成"
else
  echo "[entrypoint] 未找到模板，使用现有 openclaw.json"
fi

# ── 2. 确保目录结构完整 ───────────────────────────────────────
mkdir -p \
  "$OPENCLAW_DIR/workspace/memory" \
  "$OPENCLAW_DIR/workspace/skills" \
  "$OPENCLAW_DIR/logs" \
  "$OPENCLAW_DIR/canvas"

# ── 3. 启动 Gateway ──────────────────────────────────────────
echo "[entrypoint] 启动 openclaw gateway ..."
exec openclaw gateway run
