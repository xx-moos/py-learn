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
    const_path = os.path.join(current_dir, 'const.yaml')
    with open(const_path, 'r') as file:
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
        page.get(config['openurl'])

        
        page.ele('tag:a@@class=shortcuts-merge_requests qa-merge-requests-link')  # 查找text包含“中国日报”的元素
        page.stop_loading()


        print("开始执行页面操作...")

        print("开始点击 merge requests 链接...")
        # 等待并点击元素，使用显式等待
        shortcuts_merge_requests = page.ele('tag:a@@class=shortcuts-merge_requests qa-merge-requests-link')

        shortcuts_merge_requests.click()
        time.sleep(2)


        print("开始点击新建合并请求按钮...")

        # 尝试点击新建合并请求按钮
        new_merge_request_body_link = page.ele('tag:a@@title=新建合并请求@@id^new_merge_request_body_link')
        if new_merge_request_body_link:
            new_merge_request_body_link.click()
            print("点击了新建合并请求按钮")
        else:
            print("尝试查找替代的新建合并请求按钮...")
            new_merge_request = page.ele('tag:a@@class=btn btn-success@@title=New merge request')
            if new_merge_request:
                new_merge_request.click()
                print("点击了替代的新建合并请求按钮")

        time.sleep(1)

        # 左边分支 名字
        page.ele('tag:button@@class=dropdown-menu-toggle js-compare-dropdown js-source-branch monospace@@type=button@@data-toggle=dropdown').click()
        time.sleep(2)
        page.ele('tag:div@@class=dropdown-menu dropdown-menu-selectable js-source-branch-dropdown git-revision-dropdown show').ele('tag:li@@text()='+config['devNode']).click()
        time.sleep(2)



        # 右边分支 名字
        page.ele('tag:button@@class=dropdown-menu-toggle js-compare-dropdown js-target-branch monospace@@type=button@@data-toggle=dropdown').click()
        time.sleep(2)
        page.ele('tag:div@@class=dropdown-menu dropdown-menu-selectable js-target-branch-dropdown git-revision-dropdown show').ele('tag:li@@text()='+config['targetNode']).click()
        time.sleep(2)


        # 点击创建合并请求
        page.ele('tag:input@@type=submit@@name=commit@@class=btn btn-success mr-compare-btn').click()
        time.sleep(1)
        page.ele('tag:input@@type=submit@@name=commit@@class=btn btn-success qa-issuable-create-button').click()
        time.sleep(3)


        # 点击合并
        page.ele('tag:button@@class=qa-merge-button btn btn-sm btn-success accept-merge-request').click()

        # time.sleep(3)

        
    except Exception as e:
        print(f"发生错误: {e}")
        return None

if __name__ == "__main__":
    page = open_and_click()
