"""应用配置和设置"""
import os
from typing import List

# 修改点击事件的JavaScript脚本
JS_SCRIPT = """
function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function modifyClickEvent(event) {
    if (!event._isModified) {
        // 保存原始值（如果尚未保存）
        event._screenX = event.screenX;
        event._screenY = event.screenY;

        // 定义属性（仅一次）
        Object.defineProperty(event, 'screenX', {
            get: function() {
                return this._screenX + getRandomInt(0, 200);
            }
        });
        Object.defineProperty(event, 'screenY', {
            get: function() {
                return this._screenY + getRandomInt(0, 200);
            }
        });

        // 标记事件为已修改
        event._isModified = true;
    }
}

// 存储原始的addEventListener方法
const originalAddEventListener = EventTarget.prototype.addEventListener;

// 重写addEventListener方法
EventTarget.prototype.addEventListener = function(type, listener, options) {
    if (type === 'click') {
        const wrappedListener = function(event) {
            // 修改点击事件属性
            modifyClickEvent(event);

            // 使用修改后的事件调用原始监听器
            listener.call(this, event);
        };
        // 使用包装后的监听器调用原始addEventListener
        originalAddEventListener.call(this, type, wrappedListener, options);
    } else {
        // 对其他事件类型调用原始addEventListener
        originalAddEventListener.call(this, type, listener, options);
    }
};
"""

# 挑战检测配置
CHALLENGE_TITLES: List[str] = [
    # Cloudflare
    'Just a moment...',
    '请稍候…',
    # DDoS-GUARD
    'DDOS-GUARD',
]

CHALLENGE_SELECTORS: List[str] = [
    # Cloudflare
    '#cf-challenge-running', '.ray_id', '.attack-box', '#cf-please-wait', '#challenge-spinner', '#trk_jschal_js',
    # 为EbookParadijs、Film-Paleis、MuziekFabriek和Puur-Hollands定制的CloudFlare
    'td.info #js_info',
    # Fairlane / pararius.com
    'div.vc div.text-box h2'
]

CHALLENGE_BOX_SELECTORS: List[str] = [
    'input[name="cf-turnstile-response"]'
]

# 应用设置
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "9850"))
CHROME_PATH = os.getenv("CHROME_PATH", "/usr/bin/chromium-browser")
BROWSER_MONITOR_INTERVAL = 10  # 秒

# 应用版本配置
APP_VERSION = os.getenv("APP_VERSION", "2.0.0")

# 用户数据路径
USER_DATA_PATH = os.getenv("USER_DATA_PATH", "/var/lib/chromium/user_data")