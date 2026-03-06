FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY report.py .

# 启动脚本：将 Docker 环境变量写入 /etc/environment 供 cron 读取
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 每天 01:00 UTC（北京时间 09:00）周二至周六
RUN echo "0 1 * * 2-6 cd /app && /usr/local/bin/python3 report.py >> /var/log/market.log 2>&1" | crontab -

ENTRYPOINT ["/entrypoint.sh"]
