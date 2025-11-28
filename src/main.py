"""主FastAPI应用"""
import datetime
import uvicorn

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.config.settings import APP_HOST, APP_PORT, APP_VERSION
from src.core.browser_manager import browser_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """定义应用生命周期事件"""
    await browser_manager.start_monitoring()
    try:
        # 启动浏览器
        browser_manager.dp.latest_tab
        yield  # 等待应用运行
    finally:
        # 应用关闭逻辑
        await browser_manager.cleanup()


# 创建FastAPI应用
app = FastAPI(
    title="NAS Tools Chrome Server",
    description="基于FastAPI的Chrome自动化服务器，用于NAS工具",
    version=APP_VERSION,
    lifespan=lifespan
)

# 包含API路由
app.include_router(router)


@app.get("/")
async def root():
    """根端点，提供API信息"""
    return {
        "message": "NAS Tools Chrome Server",
        "version": APP_VERSION,
        "docs": "/docs",
        "endpoints": {
            "create_tab": "POST /tabs/",
            "list_tabs": "GET /tabs/",
            "get_html": "GET /tabs/{tab_name}/html",
            "click_element": "POST /tabs/click/",
            "close_tab": "DELETE /tabs/{tab_name}",
            "status": "GET /status"
        }
    }


@app.get("/status")
async def status():
    """健康检查端点，判断程序是否启动成功"""
    
    # 检查浏览器管理器状态
    browser_status = "initialized" if browser_manager.dp else "not_initialized"
    
    return {
        "status": "running",
        "message": "NAS Tools Chrome Server is running successfully",
        "version": APP_VERSION,
        "browser_manager": browser_status,
        "timestamp": datetime.datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run("src.main:app", host=APP_HOST, port=APP_PORT, reload=False)
