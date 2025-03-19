import asyncio
from math import log
import os
import platform
from contextlib import asynccontextmanager
import time
from typing import Dict
from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel
from DrissionPage import Chromium, ChromiumOptions
from DrissionPage.items import MixTab
from fake_useragent import UserAgent

import config
from utils import sync_cf_box_retry, sync_cf_retry


# 创建浏览器配置
def create_chromium_options() -> ChromiumOptions:
    """配置 Chromium 浏览器选项"""
    ua = UserAgent(browsers=['Edge', 'Chrome'], os=['Windows', 'Mac OS X', 'Linux'])
    co = ChromiumOptions()
    co.set_argument('--disable-webgl')
    # co.set_argument('--disable-gpu')
    co.set_argument('--lang=zh-CN')
    
    # Linux 系统特定配置
    if platform.system() == "Linux":
        co.set_argument('--no-sandbox')

    # 设置自定义浏览器路径（如果提供）
    chrome_path = os.getenv("CHROME_PATH")
    if chrome_path:
        co.set_browser_path(chrome_path)
    
    # 设置随机 User-Agent
    # co.set_user_agent(ua.random)
    return co

# 初始化全局浏览器和其他资源
chromium_options = create_chromium_options()
dp = Chromium(chromium_options)
lock = asyncio.Lock()
tabs_pool: Dict[str, MixTab] = {}  # 标签页池 {tab_name: tab_handle}

async def monitor_browser():
    """定期监控 dp 状态"""
    global dp, chromium_options
    while True:
        await asyncio.sleep(10)  # 每 10 秒检查一次
        if not dp.states.is_alive:
            logger.warning(f"检测到浏览器异常")
            async with lock:
                # 释放旧浏览器资源
                try:
                    dp.quit()
                except Exception as close_err:
                    logger.error(f"关闭浏览器时出错：{close_err}")
                # 创建新实例
                dp = Chromium(chromium_options)
                logger.info("浏览器已重启")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """定义应用生命周期事件"""
    monitor_task = asyncio.create_task(monitor_browser())
    try:
        # 启动浏览器
        dp.latest_tab
        yield  # 等待应用运行
    finally:
        monitor_task.cancel()
        # 应用关闭逻辑
        dp.quit()

app = FastAPI(lifespan=lifespan)

class NewTabRequest(BaseModel):
    url: str
    tab_name: str
    cookie: str

class ClickRequest(BaseModel):
    tab_name: str
    selector: str

class InputRequest(BaseModel):
    tab_name: str
    selector: str
    input_str: str

def create_tab_sync(request: NewTabRequest):
    global dp, tabs_pool

    # 检查是否已有同名标签页
    if request.tab_name in tabs_pool:
        raise HTTPException(status_code=400, detail="Tab name already exists.")
    
    logger.debug(f"正在访问: {request.url}")

    try:
        # 创建新标签页
        tab = dp.new_tab(request.url)
        tab.set.load_mode.none
        tab.add_init_js(config.JS_SCRIPT)
        tab.set.cookies(request.cookie)
        tab.get(request.url)

        # 执行同步逻辑
        sync_cf_retry(tab)
        # 将标签页添加到池中
        tabs_pool[request.tab_name] = tab

        return {"code": 0, "message": "Tab created", "tab_name": request.tab_name}

    except Exception as e:
        # 捕获异常并记录日志
        logger.error(f"创建标签页 {request.tab_name} 时出错: {e}")

        # 如果标签页已部分创建但失败，确保清理资源
        if 'tab' in locals() and tab:
            try:
                tab.close()
                logger.info(f"异常中已关闭标签页: {request.tab_name}")
            except Exception as cleanup_error:
                logger.error(f"清理标签页 {request.tab_name} 时出错: {cleanup_error}")

        # 返回适当的错误响应
        raise HTTPException(status_code=500, detail="Failed to create tab due to an internal error.")

def get_tab_html_sync(tab: MixTab, cf: bool = True):
    time.sleep(1)
    if cf:
        sync_cf_box_retry(tab)
        tab.stop_loading()
    html = tab.html
    logger.debug(f"获取网站 {tab.url} html成功.")
    return html

def get_tab_iframe_sync(tab: MixTab):
    iframe = tab.get_frame('t:iframe')
    logger.debug(f"获取网站 {tab.url} iframe成功.")
    return iframe.html

def get_tab_cookie_sync(tab: MixTab):
    logger.debug(f"获取网站 {tab.url} cookie成功. {tab.cookies()}")
    return '; '.join([f'{c["name"]}={c["value"]}' if c["name"] else f'{c["value"]}'  for c in tab.cookies()])

def click_on_element_sync(tab: MixTab, selector: str):
    sync_cf_box_retry(tab)
    try:
        tab.ele(selector).click(by_js=None)
    except Exception as e:
        logger.error(f"点击元素失败 {selector}: {e}")
        
def input_on_element_sync(tab: MixTab, selector:str, input_str: str):
    try:
        logger.debug(f"{tab.ele(selector)}")
        tab.actions.move_to(tab.ele(selector)).type(input_str)
    except Exception as e:
        logger.error(f"输入元素失败 {selector}: {e}")

@app.post("/tabs/")
async def create_tab(request: NewTabRequest):
    """创建新标签页"""
    try:
        result = await asyncio.to_thread(create_tab_sync, request)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tabs/")
async def list_tabs():
    """列出所有标签页"""
    global tabs_pool
    return {"tabs": list(tabs_pool.keys())}


@app.get("/tabs/{tab_name}/html")
async def get_tab_html(tab_name: str, cf: bool = True):  # 新增cf查询参数
    """获取指定标签页的 HTML 数据
    - cf: 是否需要进行内容过滤（默认True）
    """
    global dp, tabs_pool
    if tab_name not in tabs_pool:
        raise HTTPException(status_code=404, detail="Tab not found.")
    
    # 切换到指定标签页
    tab = tabs_pool.get(tab_name)
    
    try:
        # 将cf参数传递给处理函数
        html = await asyncio.to_thread(get_tab_html_sync, tab, cf=cf)
        return {"code": 0, "tab_name": tab_name, "html": html, "cf_applied": cf}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get HTML: {str(e)}")

@app.get("/tabs/{tab_name}/iframe")
async def get_tab_iframe(tab_name: str):
    """获取指定标签页的 iframe 数据"""
    global dp, tabs_pool
    if tab_name not in tabs_pool:
        raise HTTPException(status_code=404, detail="Tab not found.")
    
    # 切换到指定标签页
    tab = tabs_pool.get(tab_name)
    # 异步获取 iframe 数据
    try:
        html = await asyncio.to_thread(get_tab_iframe_sync, tab)
        return {"code": 0, "tab_name": tab_name, "html": html}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get iframe: {str(e)}")

@app.get("/tabs/{tab_name}/cookie")
async def get_tab_cookie(tab_name: str):
    """获取指定标签页的 cookie 数据"""
    global dp, tabs_pool
    if tab_name not in tabs_pool:
        raise HTTPException(status_code=404, detail="Tab not found.")
    
    # 切换到指定标签页
    tab = tabs_pool.get(tab_name)
    cookie_str = get_tab_cookie_sync(tab)
    return {"code": 0, "tab_name": tab_name, "cookie": cookie_str}

@app.post("/tabs/click/")
async def click_on_element(request: ClickRequest):
    """在指定标签页执行 JavaScript 进行点击操作"""
    global dp, tabs_pool
    if request.tab_name not in tabs_pool:
        raise HTTPException(status_code=404, detail="Tab not found.")
    
    # 切换到指定标签页
    tab = tabs_pool.get(request.tab_name)
    
    # 执行 JavaScript 代码来点击元素
    try:
        await asyncio.to_thread(click_on_element_sync, tab, request.selector)
        logger.debug(f"{tab.url} 页面点击成功.")
        return {"code": 0, "message": f"JavaScript clicked element with selector {request.selector} on tab {request.tab_name}"}
    except Exception as e:
        if 'tab' in locals() and tab:
            try:
                tab.close()
                logger.info(f"异常中已关闭标签页: {request.tab_name}")
            except Exception as cleanup_error:
                logger.error(f"清理标签页 {request.tab_name} 时出错: {cleanup_error}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    

@app.post("/tabs/input/")
async def input_on_element(request: InputRequest):
    """在指定标签页执行 JavaScript 进行输入操作"""
    global dp, tabs_pool
    if request.tab_name not in tabs_pool:
        raise HTTPException(status_code=404, detail="Tab not found.")
    
    # 切换到指定标签页
    tab = tabs_pool.get(request.tab_name)
    
    # 执行 JavaScript 代码来点击元素
    try:
        await asyncio.to_thread(input_on_element_sync, tab, request.selector, request.input_str)
        logger.debug(f"{tab.url} 页面输入元素成功.")
        return {"code": 0, "message": f"JavaScript input {request.input_str} element with selector {request.selector} on tab {request.tab_name}"}
    except Exception as e:
        if 'tab' in locals() and tab:
            try:
                tab.close()
                logger.info(f"异常中已关闭标签页: {request.tab_name}")
            except Exception as cleanup_error:
                logger.error(f"清理标签页 {request.tab_name} 时出错: {cleanup_error}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/tabs/{tab_name}/refresh")
async def refresh_tab(tab_name: str):
    """刷新页面"""
    global dp, tabs_pool
    if tab_name not in tabs_pool:
        raise HTTPException(status_code=404, detail="Tab not found.")
    
    # 切换到指定标签页
    tab = tabs_pool.get(tab_name)
    # 执行刷新命名
    try:
        await asyncio.to_thread(tab.refresh, False)
        logger.debug(f"{tab.url} 页面刷新成功.")
        return {"code": 0, "message": f"Page refresh success!"}
    except Exception as e:
        if 'tab' in locals() and tab:
            try:
                tab.close()
                logger.info(f"异常中已关闭标签页: {tab_name}")
            except Exception as cleanup_error:
                logger.error(f"清理标签页 {tab_name} 时出错: {cleanup_error}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/tabs/{tab_name}")
async def close_tab(tab_name: str):
    """关闭指定标签页"""
    global dp, tabs_pool
    if tab_name not in tabs_pool:
        raise HTTPException(status_code=404, detail="Tab not found.")
    try:
        tab = tabs_pool[tab_name]
        url = tab.url
        del tabs_pool[tab_name]
        await asyncio.to_thread(tab.close)
        logger.debug(f"{url} 对应页面已关闭.")
    except Exception as e:
        raise HTTPException(status_code=404, detail="Tab has closed.")
    return {"code": 0, "message": "Tab closed", "tab_name": tab_name}

@app.delete("/tabs/")
async def close_all_tabs():
    """关闭全部标签页"""
    global tabs_pool
    closed_tabs = []
    errors = []

    # 创建副本避免遍历时修改字典
    for tab_name in list(tabs_pool.keys()):
        try:
            tab = tabs_pool[tab_name]
            url = tab.url
            del tabs_pool[tab_name]  # 先从池中移除
            await asyncio.to_thread(tab.close)  # 异步关闭
            logger.debug(f"{url} 对应页面已关闭.")
            closed_tabs.append(tab_name)
        except Exception as e:
            errors.append(f"{tab_name}: {str(e)}")
            logger.error(f"关闭标签页 {tab_name} 失败: {e}")

    response = {
        "code": 0,
        "message": "All tabs processed",
        "closed_tabs": closed_tabs,
        "total_closed": len(closed_tabs),
        "total_errors": len(errors)
    }

    if errors:
        response["errors"] = errors

    return response