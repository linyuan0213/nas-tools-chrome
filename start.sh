#!/bin/bash

# 设置默认密码
if [ -z "$VNC_PASSWORD" ]; then
    echo "VNC_PASSWORD environment variable not set, using default password 'password'"
    export VNC_PASSWORD=password
else
    echo "Using VNC_PASSWORD from environment variable: $VNC_PASSWORD"
fi

# 替换supervisord.conf中的x11vnc密码
sed -i "s/-passwd password/-passwd $VNC_PASSWORD/g" /etc/supervisord.conf

# 启动supervisord
exec supervisord -c /etc/supervisord.conf
