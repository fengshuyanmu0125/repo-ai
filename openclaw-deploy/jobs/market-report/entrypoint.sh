#!/bin/sh
# 将容器环境变量导出到文件，使 cron job 能读取
env | grep -E "^(FEISHU_|ANTHROPIC_|FINNHUB_|TOP_N)" > /etc/environment

# 创建 wrapper 脚本，确保 cron 执行时能加载环境变量
cat > /app/run-report.sh <<'WRAPPER'
#!/bin/sh
set -a
. /etc/environment
set +a
cd /app
/usr/local/bin/python3 report.py >> /var/log/market.log 2>&1
WRAPPER
chmod +x /app/run-report.sh

# 重写 crontab，使用 wrapper 脚本
echo "0 1 * * 2-6 /app/run-report.sh" | crontab -

# 创建日志文件
touch /var/log/market.log
chmod 644 /var/log/market.log

echo "[market-report] cron 已启动，等待调度（每天 01:00 UTC / 09:00 北京时间）..."
exec cron -f
