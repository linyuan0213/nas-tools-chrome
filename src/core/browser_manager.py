"""浏览器管理和自动化功能"""
import asyncio
import os
import platform
from contextlib import asynccontextmanager
from typing import Dict, Optional

from DrissionPage import Chromium, ChromiumOptions
from DrissionPage.items import MixTab
from fake_useragent import UserAgent
from loguru import logger

from src.config.settings import JS_SCRIPT, BROWSER_MONITOR_INTERVAL, CHROME_PATH, USER_DATA_PATH


class BrowserManager:
    """管理浏览器实例和标签页操作"""
    
    def __init__(self):
        self.chromium_options = self._create_chromium_options()
        self.dp = Chromium(self.chromium_options)
        self.lock = asyncio.Lock()
        self.tabs_pool: Dict[str, MixTab] = {}
        self._monitor_task = None

    def _create_chromium_options(self) -> ChromiumOptions:
        """配置Chromium浏览器选项"""
        ua = UserAgent(browsers=['Edge', 'Chrome'], os=['Linux'])
        co = ChromiumOptions()
        
        # 基础配置
        # co.set_argument('--disable-webgl')
        co.set_argument('--disable-gpu')
        co.set_argument('--lang=zh-CN.UTF-8')
        # 移除headless模式，以便noVNC可以显示
        co.set_argument('--no-headless')
        
        # 新增Chrome参数
        co.set_argument('--no-first-run')
        co.set_argument('--force-color-profile=srgb')
        # 禁用指标记录和报告，减少browsermetrics文件生成
        co.set_argument('--disable-metrics')
        co.set_argument('--disable-metrics-reporting')
        co.set_argument('--disable-breakpad')
        co.set_argument('--disable-background-networking')
        co.set_argument('--no-report-upload')
        co.set_argument('--password-store=basic')
        co.set_argument('--use-mock-keychain')
        co.set_argument('--export-tagged-pdf')
        co.set_argument('--no-default-browser-check')
        co.set_argument('--disable-background-mode')
        co.set_argument('--enable-features=NetworkService,NetworkServiceInProcess,LoadCryptoTokenExtension,PermuteTLSExtensions')
        co.set_argument('--disable-features=FlashDeprecationWarning,EnablePasswordsAccountStorage,UMA')
        co.set_argument('--deny-permission-prompts')
        # 语言设置 - 使用完整的区域设置格式
        co.set_argument('--accept-lang=zh-CN,zh-CN.UTF-8,zh,en-US,en')
        co.set_argument('--force-language=zh-CN')
        co.set_argument('--force-lang=zh-CN.UTF-8')
        
        # Linux系统特定配置
        if platform.system() == "Linux":
            co.set_argument('--no-sandbox')
            co.set_argument('--disable-dev-shm-usage')

        co.set_user_data_path(USER_DATA_PATH)

        # 设置自定义浏览器路径（如果提供）
        if CHROME_PATH:
            co.set_browser_path(CHROME_PATH)
        
        # 设置浏览器首选项（语言相关）
        # 使用set_pref方法设置单个首选项
        co.set_pref('intl.accept_languages', 'zh-CN,zh,en-US,en')
        co.set_pref('spellcheck.dictionary', 'zh-CN')
        co.set_pref('browser.enable_spellchecking', True)
        co.set_pref('browser.spellcheck.dictionary', 'zh-CN')
        co.set_pref('translate.enabled', False)  # 禁用自动翻译
        co.set_pref('intl.selected_languages', 'zh-CN')
        co.set_pref('intl.locale.requested', 'zh-CN')
        
        # 设置随机User-Agent
        # co.set_user_agent(ua.random)
        return co

    async def monitor_browser(self):
        """定期监控浏览器状态"""
        while True:
            await asyncio.sleep(BROWSER_MONITOR_INTERVAL)
            if not self.dp.states.is_alive:
                logger.warning("检测到浏览器异常")
                async with self.lock:
                    # 释放旧浏览器资源
                    try:
                        self.dp.quit()
                    except Exception as close_err:
                        logger.error(f"关闭浏览器时出错：{close_err}")
                    # 创建新实例
                    self.dp = Chromium(self.chromium_options)
                    logger.info("浏览器已重启")

    async def start_monitoring(self):
        """启动浏览器监控任务"""
        self._monitor_task = asyncio.create_task(self.monitor_browser())

    async def stop_monitoring(self):
        """停止浏览器监控任务"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    def create_tab(self, url: str, tab_name: str, cookie: Optional[str] = None, local_storage: Optional[Dict[str, str]] = None, user_agent: Optional[str] = None) -> dict:
        """创建新的浏览器标签页"""
        # 检查是否已有同名标签页
        if tab_name in self.tabs_pool:
            raise ValueError(f"标签页名称 '{tab_name}' 已存在")
        
        logger.debug(f"正在访问: {url}")

        try:
            # 创建新标签页
            tab = self.dp.new_tab(url)
            tab.wait(1)
            tab.set.load_mode.none
            tab.add_init_js(JS_SCRIPT)
            
            # 设置User-Agent（如果提供）
            if user_agent:
                tab.set.user_agent(user_agent)
                logger.debug(f"已设置自定义User-Agent: {user_agent}")
            
            # 设置cookie（如果提供）
            if cookie:
                tab.set.cookies(cookie)
            
            # 设置local_storage（如果提供）
            if local_storage:
                for key, value in local_storage.items():
                    tab.set.local_storage(key, value)
            
            tab.get(url)

            # 将标签页添加到池中
            self.tabs_pool[tab_name] = tab

            return {"code": 0, "message": "标签页创建成功", "tab_name": tab_name}

        except Exception as e:
            # 捕获异常并记录日志
            logger.error(f"创建标签页 {tab_name} 时出错: {e}")

            # 如果标签页已部分创建但失败，确保清理资源
            if 'tab' in locals() and tab:
                try:
                    tab.close()
                    logger.info(f"异常中已关闭标签页: {tab_name}")
                except Exception as cleanup_error:
                    logger.error(f"清理标签页 {tab_name} 时出错: {cleanup_error}")

            # 返回适当的错误响应
            raise RuntimeError(f"创建标签页失败，内部错误: {e}")

    def get_tab_html(self, tab: MixTab) -> str:
        """从标签页获取HTML内容"""
        from src.utils.challenge_utils import sync_cf_box_retry
        
        sync_cf_box_retry(tab)
        tab.stop_loading()
        html = tab.html
        logger.debug(f"成功获取网站 {tab.url} 的HTML")
        return html

    def click_element(self, tab: MixTab, selector: str):
        """在标签页中点击元素"""
        from src.utils.challenge_utils import sync_cf_box_retry
        
        sync_cf_box_retry(tab)
        try:
            tab.ele(selector).click(by_js=None)
        except Exception as e:
            logger.error(f"点击元素失败 {selector}: {e}")
            raise

    def close_tab(self, tab_name: str):
        """关闭特定标签页"""
        if tab_name not in self.tabs_pool:
            raise ValueError(f"标签页 '{tab_name}' 未找到")
        
        tab = self.tabs_pool[tab_name]
        url = tab.url
        del self.tabs_pool[tab_name]
        tab.close()
        logger.debug(f"已关闭页面: {url}")

    def list_tabs(self) -> list:
        """列出所有活动标签页"""
        return list(self.tabs_pool.keys())

    def get_tab(self, tab_name: str) -> MixTab:
        """按名称获取特定标签页"""
        if tab_name not in self.tabs_pool:
            raise ValueError(f"标签页 '{tab_name}' 未找到")
        return self.tabs_pool[tab_name]

    async def cleanup(self):
        """清理浏览器资源"""
        await self.stop_monitoring()
        try:
            self.dp.quit()
        except Exception as e:
            logger.error(f"浏览器清理过程中出错: {e}")


# 全局浏览器管理器实例
browser_manager = BrowserManager()
