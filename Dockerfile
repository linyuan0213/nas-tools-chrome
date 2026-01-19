FROM python:3.11-slim

ENV CHROME_PATH=/usr/bin/chromium
ENV LANG=zh_CN.UTF-8
ENV LANGUAGE=zh_CN
ENV LC_ALL=zh_CN.UTF-8

RUN mkdir -p /app/

COPY . /app/
COPY supervisord.conf /etc/supervisord.conf
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 安装必要的软件和中文语言支持
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    xvfb \
    wget \
    chromium \
    chromium-l10n \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    locales \
    curl \
    supervisor \
    build-essential \
    x11vnc \
    net-tools \
    git \
    python3 \
    python3-pip \
    python3-numpy \
    python3-pil \
    websockify && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 生成中文区域设置
RUN echo "zh_CN.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen zh_CN.UTF-8 && \
    update-locale LANG=zh_CN.UTF-8 LANGUAGE=zh_CN:zh LC_ALL=zh_CN.UTF-8

# 安装noVNC
RUN git clone https://github.com/novnc/noVNC.git /opt/noVNC && \
    git clone https://github.com/novnc/websockify /opt/noVNC/utils/websockify && \
    ln -s /opt/noVNC/vnc.html /opt/noVNC/index.html && \
    pip install websockify

RUN pip install uv

RUN cd /app && \
    uv pip install --system -r pyproject.toml && \
    rm -rf /root/.cache

WORKDIR /app

CMD ["/start.sh"]
