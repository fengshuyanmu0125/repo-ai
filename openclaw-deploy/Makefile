.PHONY: help deploy up down restart logs logs-report shell build pull-report check-env

# ── 默认：显示帮助 ────────────────────────────────────────────
help:
	@echo ""
	@echo "OpenClaw 部署工具"
	@echo "────────────────────────────────────────"
	@echo "  make deploy       首次部署（自动检查 .env）"
	@echo "  make up           启动所有服务"
	@echo "  make down         停止所有服务"
	@echo "  make restart      重启所有服务"
	@echo "  make logs         查看 openclaw 日志"
	@echo "  make logs-report  查看日报任务日志"
	@echo "  make run-report   立即触发一次日报"
	@echo "  make shell        进入 openclaw 容器 shell"
	@echo "  make build        重新构建镜像"
	@echo "  make status       查看容器运行状态"
	@echo ""

# ── 首次部署 ──────────────────────────────────────────────────
deploy: check-env
	@echo ">>> 构建并启动所有服务..."
	docker compose up -d --build
	@echo ""
	@echo "✓ 部署完成！"
	@echo "  查看日志：make logs"
	@echo "  容器状态：make status"

# ── 日常操作 ──────────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

build:
	docker compose build --no-cache

status:
	docker compose ps

logs:
	docker compose logs -f openclaw

logs-report:
	docker compose logs -f market-report

# ── 手动触发日报 ──────────────────────────────────────────────
run-report:
	docker compose exec market-report python3 /app/report.py

# ── 进入 shell ────────────────────────────────────────────────
shell:
	docker compose exec openclaw sh

# ── 检查 .env 文件 ────────────────────────────────────────────
check-env:
	@if [ ! -f .env ]; then \
		echo ""; \
		echo "❌ 未找到 .env 文件！"; \
		echo "   请先执行：cp .env.example .env"; \
		echo "   然后编辑 .env 填写所有 API keys"; \
		echo ""; \
		exit 1; \
	fi
	@echo "✓ .env 文件已存在"
	@missing=0; \
	for key in ANTHROPIC_API_KEY FEISHU_APP_ID FEISHU_APP_SECRET FEISHU_RECEIVE_ID GATEWAY_TOKEN FINNHUB_API_KEY; do \
		val=$$(grep "^$$key=" .env | cut -d= -f2); \
		if [ -z "$$val" ] || echo "$$val" | grep -q "xxxx"; then \
			echo "  ⚠️  $$key 未配置"; \
			missing=1; \
		fi; \
	done; \
	if [ $$missing -eq 1 ]; then \
		echo ""; \
		echo "⚠️  请在 .env 中填写所有必填项后重试"; \
		exit 1; \
	fi
	@echo "✓ 所有必填配置项已检查通过"
