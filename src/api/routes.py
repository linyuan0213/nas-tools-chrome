"""API路由处理器"""
import asyncio

from fastapi import APIRouter, HTTPException
from loguru import logger

from src.api.schemas import ClickRequest, NewTabRequest
from src.core.browser_manager import browser_manager

router = APIRouter(prefix="/tabs", tags=["tabs"])


@router.post("/", response_model=dict)
async def create_tab(request: NewTabRequest):
    """创建新的浏览器标签页"""
    try:
        result = await asyncio.to_thread(
            browser_manager.create_tab, 
            request.url, 
            request.tab_name, 
            request.cookie,
            request.local_storage
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=dict)
async def list_tabs():
    """列出所有活动标签页"""
    tabs = browser_manager.list_tabs()
    return {"tabs": tabs}


@router.get("/{tab_name}/html", response_model=dict)
async def get_tab_html(tab_name: str):
    """从特定标签页获取HTML内容"""
    try:
        tab = browser_manager.get_tab(tab_name)
        html = await asyncio.to_thread(browser_manager.get_tab_html, tab)
        return {"code": 0, "tab_name": tab_name, "html": html}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取HTML失败: {str(e)}")


@router.post("/click/", response_model=dict)
async def click_on_element(request: ClickRequest):
    """在特定标签页中点击元素"""
    try:
        tab = browser_manager.get_tab(request.tab_name)
        await asyncio.to_thread(browser_manager.click_element, tab, request.selector)
        logger.debug(f"{tab.url} 页面点击成功.")
        return {
            "code": 0, 
            "message": f"在标签页 {request.tab_name} 上点击了选择器为 {request.selector} 的元素"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        if 'tab' in locals() and tab:
            try:
                tab.close()
                logger.info(f"异常中已关闭标签页: {request.tab_name}")
            except Exception as cleanup_error:
                logger.error(f"清理标签页 {request.tab_name} 时出错: {cleanup_error}")
        raise HTTPException(status_code=500, detail=f"错误: {str(e)}")


@router.delete("/{tab_name}", response_model=dict)
async def close_tab(tab_name: str):
    """关闭特定标签页"""
    try:
        await asyncio.to_thread(browser_manager.close_tab, tab_name)
        return {"code": 0, "message": "标签页已关闭", "tab_name": tab_name}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="标签页已关闭")
