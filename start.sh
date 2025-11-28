#!/bin/bash

# 启动脚本，确保所有服务正确启动

echo "启动Xvfb虚拟显示..."
Xvfb :99 -screen 0 1280x1024x24 -ac &

echo "等待Xvfb启动..."
sleep 2

echo "启动x11vnc服务..."
x11vnc -display :99 -forever -shared -nopw -listen 0.0.0.0 -rfbport 5900 &

echo "启动noVNC服务..."
websockify --web /opt/noVNC 6080 0.0.0.0:5900 &

echo "启动FastAPI应用..."
python main.py
