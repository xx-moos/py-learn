import subprocess
import sys
import os
import msvcrt


def get_current_wifi():
    """获取当前连接的WiFi名称"""
    try:
        result = subprocess.run(
            'netsh wlan show interfaces',
            capture_output=True,
            shell=True
        )
        output = result.stdout.decode('latin-1')
        for line in output.split('\n'):
            if 'SSID' in line and 'BSSID' not in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    return parts[1].strip()
    except Exception:
        pass
    return None


def connect_wifi(ssid):
    """连接到指定的WiFi"""
    print(f"\n正在连接到 {ssid} ...")
    result = subprocess.run(
        f'netsh wlan connect name="{ssid}"',
        capture_output=True,
        shell=True
    )
    output = result.stdout.decode('latin-1') + result.stderr.decode('latin-1')
    
    if '5:' in output or '拒绝访问' in output or 'denied' in output.lower():
        print("[FAIL] 权限不足！请尝试以下方法之一：")
        print("  1. 开启位置服务: 设置 -> 隐私和安全 -> 位置 -> 开启")
        print("  2. 以管理员身份运行此脚本")
        print("\n正在打开位置设置...")
        os.system('start ms-settings:privacy-location')
        return False
    
    if result.returncode == 0:
        print(f"[OK] 已成功连接到 {ssid}")
        return True
    else:
        print(f"[FAIL] 连接失败")
        return False


def select_menu(options, current_wifi=None):
    """方向键选择菜单"""
    selected = 0
    
    while True:
        # 清屏并绘制菜单
        os.system('cls')
        print("=" * 40)
        print("       WiFi 切换工具")
        print("=" * 40)
        if current_wifi:
            print(f"当前连接: {current_wifi}")
        print("-" * 40)
        print("\n使用 ↑↓ 方向键选择，Enter 确认，Esc 退出\n")
        
        for i, option in enumerate(options):
            marker = " <- 当前" if option == current_wifi else ""
            if i == selected:
                print(f"  > [{option}，{i+1}]{marker}")
            else:
                print(f"    {option}，{i+1}{marker}")
        
        # 读取按键
        key = msvcrt.getch()
        
        # 方向键是两个字节：先是 224 或 0，然后是实际键码
        if key in (b'\xe0', b'\x00'):
            key = msvcrt.getch()
            if key == b'H':  # 上
                selected = (selected - 1) % len(options)
            elif key == b'P':  # 下
                selected = (selected + 1) % len(options)
        elif key == b'\r':  # Enter
            return options[selected]
        elif key == b'\x1b':  # Esc
            return None


def main():
    wifi_list = ['tool', 'lex']
    current_wifi = get_current_wifi()
    
    selected_wifi = select_menu(wifi_list, current_wifi)
    
    os.system('cls')
    if selected_wifi is None:
        print("已退出")
    elif selected_wifi == current_wifi:
        print(f"当前已连接到 {selected_wifi}，无需切换")
    else:
        connect_wifi(selected_wifi)
    
    print("\n按任意键退出...")
    msvcrt.getch()


if __name__ == "__main__":
    main()
