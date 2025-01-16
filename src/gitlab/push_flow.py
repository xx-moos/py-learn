import platform
from DrissionPage import ChromiumOptions, Chromium, ChromiumPage
import subprocess
import time
import psutil
import signal
import os
import shutil
import stat
import yaml



# 读取const.yaml文件
def get_const():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    const_path = os.path.join(current_dir, 'const.yaml')
    with open(const_path, 'r') as file:
        return yaml.safe_load(file)



def open_and_click():

    # 创建配置对象
    co = ChromiumOptions()
    co.set_local_port(9333)
    
    # 设置用户文件夹路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    user_data_path = os.path.join(project_root, 'user-files')
    print(f"yong ->  用户数据路径: {user_data_path}")
    
    # 设置用户数据路径
    co.set_user_data_path(user_data_path)
    
    # 设置其他选项以确保更好的兼容性
    co.set_argument('--disable-web-security')  # 禁用跨域限制
    co.set_argument('--no-first-run')  # 禁用首次运行提示
    co.set_argument('--no-default-browser-check')  # 禁用默认浏览器检查
    
    try:
        # 创建浏览器对象
        browser = Chromium(co)

        config = get_const()

        # 获取最新标签页
        page = browser.latest_tab

        time.sleep(6)
        
        # 打开网址
        page.get(config['openurl'])
        
        time.sleep(5)
        
        # 等待并点击元素
        shortcuts_merge_requests = page.ele('tag:a@@class=shortcuts-merge_requests qa-merge-requests-link')
        shortcuts_merge_requests.click()
        time.sleep(3)

        new_merge_request_body_link = page.ele('tag:a@@title=新建合并请求@@id^new_merge_request_body_link')
        if new_merge_request_body_link:
            new_merge_request_body_link.click()
        else:
            print("未找到元素 new_merge_request_body_link")
            new_merge_request = page.ele('tag:a@@class=btn btn-success@@title=New merge request')
            if new_merge_request:
                new_merge_request.click()
        

        time.sleep(2)
        



        
    except Exception as e:
        print(f"发生错误: {e}")
        return None

if __name__ == "__main__":
    page = open_and_click()
