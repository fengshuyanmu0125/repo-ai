FROM node:22-slim

# 系统依赖：Python3（MCP server）+ envsubst（配置模板替换）+ curl + openssh-client
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    openssh-client \
    gettext-base \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# 配置 git 使用 https 替代 ssh（避免 ssh 认证问题）
RUN git config --global url."https://github.com/".insteadOf "ssh://git@github.com/" && \
    git config --global url."https://github.com/".insteadOf "git@github.com:"

# Python 虚拟环境（避免 externally-managed-environment 报错）
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Python 依赖（增加超时和重试，使用清华镜像加速）
RUN pip install --no-cache-dir \
    --timeout 300 \
    --retries 5 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    yfinance \
    pandas \
    requests \
    mcp \
    fastmcp

# 安装 openclaw（当前正式包名）
RUN npm install -g openclaw

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
