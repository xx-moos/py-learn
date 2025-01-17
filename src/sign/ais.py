import platform
from DrissionPage import ChromiumOptions, Chromium, ChromiumPage
from DrissionPage.common import Settings
import subprocess
import time
import psutil
import signal
import os
import shutil
import stat
import yaml
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.open_browser_old_user_data import open_browser


yifengUrl = "https://api.ephone.ai/panel"
aiccUrl = "https://aicnn.cn/pay"
wochirouUrl = "https://wochirou.com/dashboard/token"


def yf_click():
    try:
        # 创建浏览器对象
        browser = open_browser()

        # 获取最新标签页
        page = browser.latest_tab
        # page.set.load_mode.none()

        # 打开目标网址
        print("打开目标网址...")
        page.get(yifengUrl)
        time.sleep(3)

        page.ele("tag:div@@class=semi-calendar-month-week@@role=presentation")
        page.stop_loading()

        print("开始执行页面操作...")

        okBtn = page.ele(
            "tag:button@@class=semi-button semi-button-primary@@type=button@@aria-disabled=false@@text()=确定"
        )
        if okBtn:
            okBtn.click()
            time.sleep(1)

        page.ele("tag:div@@id=semiTabcheckin").click()
        time.sleep(1)

        page.ele("tag:li@@class=semi-calendar-today semi-calendar-month-same").ele(
            "tag:div@@class=semi-tag-content semi-tag-content-center@@text()=去签到"
        ).click()
        time.sleep(2)
        
        
        
        

    except Exception as e:
        print(f"yf  发生错误: {e}")
        return None


def aicc_click():
    try:
        # 创建浏览器对象
        browser = open_browser()

        # 获取最新标签页
        page = browser.latest_tab
        # page.set.load_mode.none()

        # 打开目标网址
        print("打开目标网址...")
        page.get(aiccUrl)
        time.sleep(3)

        ele = page.ele("tag:button@@class=signBtn1")
        page.stop_loading()

        print("开始执行页面操作...")
        
        page.scroll.to_see(ele)

        ele.click()
        time.sleep(1)
        page.refresh()

        
        

    except Exception as e:
        print(f"发生错误: {e}")
        return None


def wochi_click():
    try:
        # 创建浏览器对象
        browser = open_browser()

        # 获取最新标签页
        page = browser.latest_tab

        # 打开目标网址
        print("打开目标网址...")
        page.get(wochirouUrl)
        time.sleep(3)

        ele = page.ele("tag:span@@text()=linuxdo_1615")
        page.stop_loading()

        print("开始执行页面操作...")
        
        ele.hover()

    except Exception as e:
        print(f"发生错误: {e}")
        return None


if __name__ == "__main__":
    yf_click()
    time.sleep(1)
    aicc_click()
    time.sleep(1)
    wochi_click()
