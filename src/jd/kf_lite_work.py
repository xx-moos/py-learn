#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
京东前端项目自动化部署脚本
作者：老王 (暴躁技术流)
功能：自动执行bun build:pre，重命名文件夹，复制到指定目录
"""

import os
import sys
import subprocess
import shutil
import re
import time
import threading
from pathlib import Path
from typing import Optional

# 颜色输出常量
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message: str, color: str = Colors.WHITE) -> None:
    """带颜色的输出，老王专用"""
    print(f"{color}{message}{Colors.ENDC}")

def print_error(message: str) -> None:
    """错误信息输出"""
    print_colored(f"❌ 艹！{message}", Colors.RED)

def print_success(message: str) -> None:
    """成功信息输出"""
    print_colored(f"✅ 乖乖！{message}", Colors.GREEN)

def print_info(message: str) -> None:
    """普通信息输出"""
    print_colored(f"ℹ️  {message}", Colors.CYAN)

def print_warning(message: str) -> None:
    """警告信息输出"""
    print_colored(f"⚠️  {message}", Colors.YELLOW)

def show_spinner(message: str, stop_event: threading.Event) -> None:
    """显示加载动画"""
    spinner_chars = "|/-\\"
    i = 0
    while not stop_event.is_set():
        print(f"\r{Colors.CYAN}{message} {spinner_chars[i % len(spinner_chars)]}{Colors.ENDC}", end="", flush=True)
        time.sleep(0.1)
        i += 1
    print(f"\r{' ' * (len(message) + 2)}\r", end="", flush=True)

class KfLiteDeployment:
    def __init__(self):
        """初始化部署配置"""
        self.source_dir = Path("E:/code/fe/JD/kf-manage-lite")
        self.build_output_dir = self.source_dir / "kf-manage-lite"
        self.target_parent_dir = Path("E:/code/fe/JD/staticDeploy")
        self.target_folder_name = ""
        # 继承系统环境变量，确保能找到bun等工具
        self.env = os.environ.copy()

    def validate_paths(self) -> bool:
        """验证路径是否存在"""
        if not self.source_dir.exists():
            print_error(f"源目录不存在：{self.source_dir}")
            return False

        if not self.target_parent_dir.exists():
            print_error(f"目标父目录不存在：{self.target_parent_dir}")
            print_info("老王我尝试创建目标目录...")
            try:
                self.target_parent_dir.mkdir(parents=True, exist_ok=True)
                print_success(f"目标目录创建成功：{self.target_parent_dir}")
            except Exception as e:
                print_error(f"创建目标目录失败：{e}")
                return False

        return True

    def run_build_command(self) -> bool:
        """执行构建命令"""
        print_info(f"切换到目录：{self.source_dir}")

        # 检查bun是否可用
        try:
            result = subprocess.run(
                ["bun", "--version"],
                capture_output=True,
                text=True,
                cwd=self.source_dir,
                env=self.env,  # 使用继承的系统环境变量
                shell=True
            )
            if result.returncode != 0:
                print_error("bun命令不可用，请确保已安装bun！")
                return False
            print_info(f"检测到bun版本：{result.stdout.strip()}")
        except FileNotFoundError:
            print_error("找不到bun命令，请确保bun已安装并在PATH中！")
            return False

        print_info("开始执行 bun build:pre...")

        # 创建停止事件用于控制spinner
        stop_spinner = threading.Event()
        spinner_thread = threading.Thread(
            target=show_spinner,
            args=("构建中", stop_spinner)
        )
        spinner_thread.start()

        try:
            # 执行构建命令
            process = subprocess.Popen(
                ["bun", "build:pre"],
                cwd=self.source_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                env=self.env,  # 使用继承的系统环境变量
                shell=True  # Windows需要shell=True
            )

            stdout, stderr = process.communicate()

            # 停止spinner
            stop_spinner.set()
            spinner_thread.join()

            if process.returncode == 0:
                print_success("构建完成！")
                if stdout.strip():
                    print_info("构建输出：")
                    print(stdout)
                return True
            else:
                print_error("构建失败！")
                if stderr.strip():
                    print_error("错误信息：")
                    print_colored(stderr, Colors.RED)
                if stdout.strip():
                    print_info("构建输出：")
                    print(stdout)
                return False

        except Exception as e:
            stop_spinner.set()
            spinner_thread.join()
            print_error(f"构建过程出错：{e}")
            return False

    def rename_build_output(self) -> bool:
        """重命名构建输出文件夹"""
        if not self.build_output_dir.exists():
            print_error(f"构建输出目录不存在：{self.build_output_dir}")
            return False

        new_name = self.source_dir / self.target_folder_name

        try:
            if new_name.exists():
                print_warning(f"目标名称已存在，先删除：{new_name}")
                if new_name.is_dir():
                    shutil.rmtree(new_name)
                else:
                    new_name.unlink()

            self.build_output_dir.rename(new_name)
            print_success(f"文件夹重命名成功：{self.build_output_dir.name} -> {self.target_folder_name}")
            self.build_output_dir = new_name  # 更新路径引用
            return True

        except Exception as e:
            print_error(f"重命名失败：{e}")
            return False

    def copy_to_target(self) -> bool:
        """复制文件夹到目标目录"""
        target_path = self.target_parent_dir / self.target_folder_name

        try:
            if target_path.exists():
                print_warning(f"目标路径已存在，先删除：{target_path}")
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()

            print_info(f"开始复制文件夹到：{target_path}")

            # 显示复制进度
            stop_spinner = threading.Event()
            spinner_thread = threading.Thread(
                target=show_spinner,
                args=("复制中", stop_spinner)
            )
            spinner_thread.start()

            shutil.copytree(self.build_output_dir, target_path)

            stop_spinner.set()
            spinner_thread.join()

            print_success(f"复制完成！目标路径：{target_path}")
            return True

        except Exception as e:
            if 'stop_spinner' in locals():
                stop_spinner.set()
                spinner_thread.join()
            print_error(f"复制失败：{e}")
            return False

    def validate_folder_name(self, folder_name: str) -> bool:
        """验证文件夹名称是否合法"""
        if not folder_name or not folder_name.strip():
            print_error("文件夹名称不能为空，憨批！")
            return False

        # Windows文件夹名称不能包含的字符
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, folder_name):
            print_error(f"文件夹名称包含非法字符！这些SB字符不能用：< > : \" / \\ | ? *")
            return False

        # 不能以点结尾
        if folder_name.endswith('.'):
            print_error("文件夹名称不能以点结尾，这是Windows的SB规则！")
            return False

        # 保留名称检查
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3',
                         'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        if folder_name.upper() in reserved_names:
            print_error(f"'{folder_name}' 是Windows保留名称，不能用这个SB名字！")
            return False

        return True

    def get_user_input(self) -> Optional[str]:
        """获取用户输入的文件夹名称"""
        print_colored("\n" + "="*60, Colors.MAGENTA)
        print_colored("老王牌京东前端自动化部署工具", Colors.MAGENTA + Colors.BOLD)
        print_colored("="*60, Colors.MAGENTA)

        print_info("当前配置：")
        print_info(f"  源目录: {self.source_dir}")
        print_info(f"  构建输出: {self.build_output_dir}")
        print_info(f"  目标目录: {self.target_parent_dir}")

        while True:
            try:
                folder_name = input(f"\n{Colors.YELLOW}请输入新的文件夹名称（老王我会把kf-manage-lite重命名为这个）: {Colors.ENDC}").strip()

                if folder_name.lower() in ['exit', 'quit', '退出', 'q']:
                    print_warning("老王我撤了，拜拜！")
                    return None

                if self.validate_folder_name(folder_name):
                    # 检查目标目录是否已存在同名文件夹
                    target_path = self.target_parent_dir / folder_name
                    if target_path.exists():
                        print_warning(f"目标目录已存在文件夹 '{folder_name}'")
                        choice = input(f"{Colors.YELLOW}要覆盖吗？(y/n): {Colors.ENDC}").strip().lower()
                        if choice in ['y', 'yes', '是', 'Y']:
                            return folder_name
                        else:
                            print_info("换个名字吧，憨批！")
                            continue
                    return folder_name

            except KeyboardInterrupt:
                print_warning("\n\n老王我被中断了，再见！")
                return None
            except Exception as e:
                print_error(f"输入出错了：{e}")

    def deploy(self) -> bool:
        """执行完整的部署流程"""
        print_colored("\n开始部署流程...", Colors.BOLD)

        # 1. 验证路径
        if not self.validate_paths():
            return False

        # 2. 执行构建
        if not self.run_build_command():
            return False

        # 3. 重命名文件夹
        if not self.rename_build_output():
            return False

        # 4. 复制到目标目录
        if not self.copy_to_target():
            return False

        print_colored("\n" + "="*60, Colors.GREEN)
        print_success("部署完成！老王我牛逼不？")
        print_colored("="*60, Colors.GREEN)
        print_info(f"最终目标路径：{self.target_parent_dir / self.target_folder_name}")

        return True

def main():
    """主函数"""
    try:
        deployer = KfLiteDeployment()

        # 获取用户输入
        folder_name = deployer.get_user_input()
        if not folder_name:
            sys.exit(0)

        deployer.target_folder_name = folder_name
        print_success(f"好嘞！老王我开始部署，目标文件夹名称：{folder_name}")

        # 执行部署
        if deployer.deploy():
            print_success("老王我搞定了！")
            sys.exit(0)
        else:
            print_error("部署失败，老王我也很无奈...")
            sys.exit(1)

    except Exception as e:
        print_error(f"程序崩了：{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()