from typing import Tuple
from loguru import logger
from DrissionPage.items import MixTab
from pyquery import PyQuery

from config import CHALLENGE_BOX_SELECTORS, CHALLENGE_SELECTORS, CHALLENGE_TITLES

def under_challenge(html_text: str):
    """
    Check if the page is under challenge
    :param html_text:
    :return:
    """
    # get the page title
    if not html_text:
        return False
    page_title = PyQuery(html_text)('title').text()
    logger.debug("under_challenge page_title=" + page_title)
    for title in CHALLENGE_TITLES:
        if page_title.lower() == title.lower():
            return True
    for selector in CHALLENGE_SELECTORS:
        html_doc = PyQuery(html_text)
        if html_doc(selector):
            return True
    return False

def under_box_challenge(html_text: str):
    """
    Check if the page is under challenge
    :param html_text:
    :return:
    """
    if not html_text:
        return False
    for selector in CHALLENGE_BOX_SELECTORS:
        html_doc = PyQuery(html_text)
        if html_doc(selector):
            return True
    return False

def sync_cf_retry(page: MixTab, tries: int = 5) -> Tuple[bool, bool]:
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
            cf_iframe = cf_wrapper.shadow_root.ele("tag:iframe",timeout=3)

            box = cf_iframe.ele('tag:body').shadow_root
            cf_button = box.ele("tag:input")
            cf_button.click()
        except Exception as e:
            page.wait(1)
            logger.debug(f"DrissionPage Error: {e}")
            success = False
        tries -= 1
    if tries == user_tries:
        cf = False
    return success, cf


def sync_cf_box_retry(page: MixTab, tries: int = 3) -> Tuple[bool, bool]:
    success = False
    cf = True
    user_tries = tries
    while tries > 0:
        # 非CF网站
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
            cf_iframe = cf_wrapper.shadow_root.ele("tag:iframe",timeout=3)

            box = cf_iframe.ele('tag:body').shadow_root
            try:
                cf_button = box.ele("tag:input")
                cf_button.click()
            except Exception as e:
                pass
            visibility = box.ele('tag:div@id=success').style('visibility')
            if visibility == 'visible':
                success=True
                break
        except Exception as e:
            page.wait(1)
            logger.debug(f"DrissionPage Error: {e}")
            success = False
        tries -= 1
    if tries == user_tries:
        cf = False
    return success, cf