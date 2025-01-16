from DrissionPage import ChromiumOptions, Chromium, ChromiumPage
import subprocess
import time
import psutil
import signal
import os
import shutil



# 准备当前的谷歌用户数据
def prepare_user_data():
    """只复制必要的用户数据文件"""
    chrome_user_data = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default')
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    user_data_path = os.path.join(project_root, 'user-file', 'Default')
    
    # 需要复制的文件列表
    files_to_copy = [
        'Cookies',
        'Login Data',
        'Web Data',
    ]
    
    try:
        # 确保目标目录存在
        os.makedirs(user_data_path, exist_ok=True)
        
        # 复制指定文件
        for file in files_to_copy:
            src = os.path.join(chrome_user_data, file)
            dst = os.path.join(user_data_path, file)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"已复制: {file}")
                
        return True
        
    except Exception as e:
        print(f"复制用户数据时发生错误: {e}")
        return False

def open_and_click():
    # 首先准备用户数据
    if not prepare_user_data():
        print("用户数据准备失败，将使用空白配置")
    
    time.sleep(6)

    # 创建配置对象
    co = ChromiumOptions()
    co.set_local_port(9333)
    
    # 设置用户文件夹路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    user_data_path = os.path.join(project_root, 'user-file')
    print(f"用户数据路径: {user_data_path}")
    
    # 确保用户文件夹存在
    if not os.path.exists(user_data_path):
        os.makedirs(user_data_path)
    
    # 设置用户数据路径
    co.set_user_data_path(user_data_path)
    
    try:
        # 创建浏览器对象
        browser = Chromium(co)

        time.sleep(3)

        # 获取最新标签页
        page = browser.latest_tab
        
        # 访问网址
        page.get('https://www.example.com')
        
        # 等待并点击元素
        element = page.ele('h1')
        element.click()
        
        return page
        
    except Exception as e:
        print(f"发生错误: {e}")
        return None

if __name__ == "__main__":
    page = open_and_click()
