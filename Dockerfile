FROM python:3.11-slim

ENV CHROME_PATH=/usr/bin/chromium
ENV LANG=zh_CN.UTF-8
ENV LANGUAGE=zh_CN

RUN mkdir -p /app/

COPY ./*.txt ./*.py /app/
COPY supervisord.conf /etc/supervisord.conf

# 安装必要的软件
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    xvfb \
    wget \
    chromium \
    fonts-noto-cjk \
    curl \
    supervisor \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    cd /app && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache

WORKDIR /app

CMD ["supervisord", "-c", "/etc/supervisord.conf"]