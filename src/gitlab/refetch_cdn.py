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


# 读取const.yaml文件
def get_const():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    const_path = os.path.join(current_dir, "const.yaml")
    with open(const_path, "r") as file:
        return yaml.safe_load(file)


def open_and_click():
    try:
        config = get_const()

        # 创建浏览器对象
        browser = open_browser()

        # 获取最新标签页
        page = browser.latest_tab
        page.set.load_mode.none()

        # 打开目标网址
        print("打开目标网址...")
        page.get(config["cdnOpenUrl"])

        page.ele("tag:textarea@@id=url")
        page.stop_loading()

        print("开始执行页面操作...")

        page.ele("tag:textarea@@id=url").focus()
        for index, i in enumerate(config["cdnUrl"]):
            page.ele("tag:textarea@@id=url").input(i)
            if index != len(config["cdnUrl"]) - 1:
                page.actions.key_down("ENTER")

        time.sleep(1.5)
        page.ele("tag:button@@class=ant-btn ant-btn-primary@@type=submit").click()

        # time.sleep(3)

    except Exception as e:
        print(f"发生错误: {e}")
        return None


if __name__ == "__main__":
    page = open_and_click()
