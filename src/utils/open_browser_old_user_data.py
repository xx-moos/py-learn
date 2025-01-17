import platform
from DrissionPage import ChromiumOptions, Chromium
import os


def get_browser_options():
    # 创建配置对象
    co = ChromiumOptions()
    co.set_local_port(9333)
    system = get_system()
    # 设置用户文件夹路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    user_data_path = ''
    if system == 'Windows':
        user_data_path = os.path.join(project_root, 'dpconfig/user-files', 'User Data')
    else:
        user_data_path = os.path.join(project_root, 'dpconfig/user-files')

    print(f"yong ->  用户数据路径: {user_data_path}")
    
    # 设置用户数据路径
    co.set_user_data_path(user_data_path)
    
    # 设置其他选项以确保更好的兼容性
    co.set_argument('--disable-web-security')  # 禁用跨域限制
    co.set_argument('--no-first-run')  # 禁用首次运行提示
    co.set_argument('--no-default-browser-check')  # 禁用默认浏览器检查
    
    return co

# 区分系统
def get_system():
    system = platform.system()
    return system

def open_browser():
    co = get_browser_options()
    browser = Chromium(co)
    return browser


# 如果有其他函数，也需要在这里导出
__all__ = ['open_browser']