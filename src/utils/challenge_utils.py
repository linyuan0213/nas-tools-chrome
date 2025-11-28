"""挑战检测和处理工具"""
from typing import Tuple

from DrissionPage.items import MixTab
from loguru import logger
from pyquery import PyQuery

from src.config.settings import CHALLENGE_BOX_SELECTORS, CHALLENGE_SELECTORS, CHALLENGE_TITLES


def under_challenge(html_text: str) -> bool:
    """
    检查页面是否处于挑战状态
    
    Args:
        html_text: 要检查的HTML内容
        
    Returns:
        bool: 如果页面处于挑战状态则为True，否则为False
    """
    # 获取页面标题
    if not html_text:
        return False
        
    page_title = PyQuery(html_text)('title').text()
    logger.debug(f"under_challenge page_title={page_title}")
    
    for title in CHALLENGE_TITLES:
        if page_title.lower() == title.lower():
            return True
            
    for selector in CHALLENGE_SELECTORS:
        html_doc = PyQuery(html_text)
        if html_doc(selector):
            return True
            
    return False


def under_box_challenge(html_text: str) -> bool:
    """
    检查页面是否处于盒子挑战状态
    
    Args:
        html_text: 要检查的HTML内容
        
    Returns:
        bool: 如果页面处于盒子挑战状态则为True，否则为False
    """
    if not html_text:
        return False
        
    for selector in CHALLENGE_BOX_SELECTORS:
        html_doc = PyQuery(html_text)
        if html_doc(selector):
            return True
            
    return False


def sync_cf_retry(page: MixTab, tries: int = 5) -> Tuple[bool, bool]:
    """
    同步重试CloudFlare挑战解决
    
    Args:
        page: 浏览器页面/标签页
        tries: 重试尝试次数
        
    Returns:
        Tuple[bool, bool]: (成功, 是否挑战)
    """
    success = False
    cf = True
    user_tries = tries
    
    while tries > 0:
        # 非CF网站
        if not under_challenge(page.html):
            success = True
            break
            
        try:
            page.wait(5)
            if not under_challenge(page.html):
                success = True
                break
                
            cf_solution = page.ele('tag:input@name=cf-turnstile-response', timeout=3)
            cf_wrapper = cf_solution.parent()
            cf_iframe = cf_wrapper.shadow_root.ele("tag:iframe", timeout=3)

            box = cf_iframe.ele('tag:body').shadow_root
            cf_button = box.ele("tag:input")
            cf_button.click()
            
        except Exception as e:
            page.wait(1)
            logger.debug(f"DrissionPage 错误: {e}")
            success = False
            
        tries -= 1
        
    if tries == user_tries:
        cf = False
        
    return success, cf


def sync_cf_box_retry(page: MixTab, tries: int = 3) -> Tuple[bool, bool]:
    """
    同步重试CloudFlare盒子挑战解决
    
    Args:
        page: Browser page/tab
        tries: Number of retry attempts
        
    Returns:
        Tuple[bool, bool]: (success, was_challenge)
    """
    success = False
    cf = True
    user_tries = tries
    
    while tries > 0:
        # Non-CF website
        if not under_box_challenge(page.html):
            success = True
            break
            
        try:
            page.wait(5)
            if not under_box_challenge(page.html):
                success = True
                break
                
            cf_solution = page.ele('tag:input@name=cf-turnstile-response', timeout=3)
            cf_wrapper = cf_solution.parent()
            cf_iframe = cf_wrapper.shadow_root.ele("tag:iframe", timeout=3)

            box = cf_iframe.ele('tag:body').shadow_root
            try:
                cf_button = box.ele("tag:input")
                cf_button.click()
            except Exception as e:
                pass
                
            visibility = box.ele('tag:div@id=success').style('visibility')
            if visibility == 'visible':
                success = True
                break
                
        except Exception as e:
            page.wait(1)
            logger.debug(f"DrissionPage Error: {e}")
            success = False
            
        tries -= 1
        
    if tries == user_tries:
        cf = False
        
    return success, cf
