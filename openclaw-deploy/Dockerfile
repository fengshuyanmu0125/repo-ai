# syntax=docker/dockerfile:1
FROM node:22-slim

# 系统依赖（单层合并，利用缓存）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git openssh-client gettext-base \
    python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

# git https 替代 ssh
RUN git config --global url."https://github.com/".insteadOf "ssh://git@github.com/" && \
    git config --global url."https://github.com/".insteadOf "git@github.com:"

# Python 虚拟环境
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Python 依赖（使用 BuildKit 缓存挂载）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
    --timeout 300 --retries 5 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    yfinance pandas requests mcp fastmcp

# npm 全局安装 openclaw（使用 BuildKit 缓存挂载）
RUN npm config set registry https://registry.npmmirror.com
RUN --mount=type=cache,target=/root/.npm \
    npm install -g openclaw

# ── 复制配置到 openclaw 目录 ───────────────────────────────────
WORKDIR /root/.openclaw

# 创建运行时目录（credentials/identity/devices 通过 volume 挂载）
RUN mkdir -p credentials identity devices workspace/memory workspace/skills logs canvas

COPY config/openclaw.tmpl.json  ./openclaw.tmpl.json
COPY plugins/                   ./plugins/
COPY workspace/                 ./workspace/

# ── 启动脚本 ──────────────────────────────────────────────────
COPY docker-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 18789

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
