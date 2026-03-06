#!/bin/sh
# 将容器环境变量写入 /etc/environment，使 cron job 能读取
printenv | grep -E "^(FEISHU_|ANTHROPIC_|FINNHUB_|TOP_N)" > /etc/environment

# 创建日志文件
touch /var/log/market.log
chmod 644 /var/log/market.log

echo "[market-report] cron 已启动，等待调度（每天 01:00 UTC）..."
exec cron -f
