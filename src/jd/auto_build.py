#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
京东 kf-manage-lite 项目自动打包部署脚本
作者：老王
功能：自动执行打包并部署到 staticDeploy
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time

# 艹，这些路径配置必须准确，不然又要报错
PROJECT_DIR = r"E:\code\fe\JD\kf-manage-lite"
STATIC_DEPLOY_DIR = r"E:\code\fe\JD\staticDeploy"
BUILD_OUTPUT_DIR = os.path.join(PROJECT_DIR, "kf-manage-lite")
DEPLOY_TARGET_DIR = os.path.join(STATIC_DEPLOY_DIR, "kf-manage-lite")


class AutoBuilder:
    """自动打包部署类 - 老王出品，必属精品"""

    def __init__(self):
        """初始化，继承所有系统环境变量"""
        # 继承系统环境变量，确保能找到 bun 和 git
        self.env = os.environ.copy()
        self.errors = []

    def log(self, message, level="INFO"):
        """输出日志信息"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def check_command(self, command):
        """检查命令是否可用"""
        try:
            result = subprocess.run(
                f"where {command}" if sys.platform == "win32" else f"which {command}",
                shell=True,
                capture_output=True,
                text=True,
                env=self.env
            )
            if result.returncode == 0:
                self.log(f"✓ {command} 命令可用：{result.stdout.strip()}")
                return True
            else:
                self.log(f"✗ {command} 命令不可用，艹，检查一下你的环境变量！", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ 检查 {command} 命令时出错：{str(e)}", "ERROR")
            return False

    def run_command(self, command, cwd=None, description=""):
        """执行命令并实时输出"""
        self.log(f"执行：{description or command}")

        try:
            # 使用 Popen 以便实时获取输出
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=cwd,
                env=self.env,
                encoding='utf-8',
                errors='ignore'
            )

            # 实时输出命令执行结果
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(f"  > {line.rstrip()}")

            return_code = process.wait()

            if return_code == 0:
                self.log(f"✓ {description or '命令'}执行成功")
                return True
            else:
                self.log(f"✗ {description or '命令'}执行失败，返回码：{return_code}", "ERROR")
                return False

        except Exception as e:
            self.log(f"✗ 执行命令出错：{str(e)}", "ERROR")
            return False

    def build_project(self):
        """执行项目打包"""
        self.log("=" * 60)
        self.log("开始打包 kf-manage-lite 项目")

        # 检查项目目录
        if not os.path.exists(PROJECT_DIR):
            self.log(f"✗ 项目目录不存在：{PROJECT_DIR}", "ERROR")
            return False

        # 切换到项目目录并执行打包
        return self.run_command(
            "bun build:pre",
            cwd=PROJECT_DIR,
            description="执行 bun build:pre 打包命令"
        )

    def git_pull_static_deploy(self):
        """在 staticDeploy 目录执行 git pull"""
        self.log("=" * 60)
        self.log("更新 staticDeploy 仓库")

        # 检查目录
        if not os.path.exists(STATIC_DEPLOY_DIR):
            self.log(f"✗ staticDeploy 目录不存在：{STATIC_DEPLOY_DIR}", "ERROR")
            return False

        # 执行 git pull
        return self.run_command(
            "git pull",
            cwd=STATIC_DEPLOY_DIR,
            description="拉取 staticDeploy 最新代码"
        )

    def copy_build_output(self):
        """复制打包产物到部署目录"""
        self.log("=" * 60)
        self.log("复制打包产物到部署目录")

        # 检查源目录
        if not os.path.exists(BUILD_OUTPUT_DIR):
            self.log(f"✗ 打包输出目录不存在：{BUILD_OUTPUT_DIR}", "ERROR")
            self.log("  可能是打包失败了，检查一下上面的错误信息", "ERROR")
            return False

        try:
            # 如果目标目录存在，先删除
            if os.path.exists(DEPLOY_TARGET_DIR):
                self.log(f"删除旧的部署目录：{DEPLOY_TARGET_DIR}")
                shutil.rmtree(DEPLOY_TARGET_DIR)

            # 复制文件夹
            self.log(f"复制：{BUILD_OUTPUT_DIR}")
            self.log(f"  到：{DEPLOY_TARGET_DIR}")
            shutil.copytree(BUILD_OUTPUT_DIR, DEPLOY_TARGET_DIR)

            # 统计文件数量
            file_count = sum(1 for _ in Path(DEPLOY_TARGET_DIR).rglob("*") if _.is_file())
            self.log(f"✓ 复制完成，共 {file_count} 个文件")
            return True

        except Exception as e:
            self.log(f"✗ 复制文件时出错：{str(e)}", "ERROR")
            return False

    def run(self):
        """执行完整的打包部署流程"""
        print("\n" + "=" * 60)
        print("    京东 kf-manage-lite 自动打包部署脚本")
        print("    老王出品 - 简洁高效，拒绝花里胡哨")
        print("=" * 60 + "\n")

        # 1. 检查必要的命令
        self.log("检查环境...")
        if not self.check_command("bun"):
            self.log("艹，bun 都没装，还打包个锤子！", "ERROR")
            return False

        if not self.check_command("git"):
            self.log("git 也没有？你这环境太垃圾了！", "ERROR")
            return False

        # 2. 执行打包
        if not self.build_project():
            self.log("打包失败了，艹，检查一下代码有没有问题！", "ERROR")
            return False

        # 3. 更新 staticDeploy
        if not self.git_pull_static_deploy():
            self.log("git pull 失败，可能有冲突，手动处理一下吧", "WARNING")
            # 询问是否继续
            response = input("\n是否继续复制文件？(y/n): ")
            if response.lower() != 'y':
                self.log("用户取消操作")
                return False

        # 4. 复制打包产物
        if not self.copy_build_output():
            self.log("复制文件失败，艹，检查一下权限问题！", "ERROR")
            return False

        # 完成
        print("\n" + "=" * 60)
        self.log("🎉 所有操作完成！打包部署成功！", "SUCCESS")
        self.log(f"部署路径：{DEPLOY_TARGET_DIR}")
        print("=" * 60 + "\n")

        return True


def main():
    """主函数"""
    builder = AutoBuilder()

    try:
        success = builder.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断操作，艹，不玩了！")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n出现未知错误：{str(e)}")
        print("艹，这个错误老王也没见过，自己看着办吧！")
        sys.exit(1)


if __name__ == "__main__":
    main()
