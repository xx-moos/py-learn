#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开始操作 kf-manage-lite yufa-http  分支  这个发布的是 http
---------------------------------------------------------------------------
自动打包部署脚本
功能:自动执行打包并部署到 staticDeploy 的 yufa 分支  
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time

# 艹,这些路径配置必须准确,不然又要报错
PROJECT_DIR = r"E:\code\fe\JD\kf-manage-lite"
STATIC_DEPLOY_DIR = r"E:\code\fe\JD\staticDeploy"
BUILD_OUTPUT_DIR = os.path.join(PROJECT_DIR, "kf-manage-lite")
DEPLOY_TARGET_DIR = os.path.join(STATIC_DEPLOY_DIR, "kf-manage-lite-http")


class AutoBuilder:
    """新的预发分支打包，也就是新的文件夹，不占用原本预发分支"""

    def __init__(self):
        """初始化,继承所有系统环境变量"""
        # 继承系统环境变量,确保能找到 bun 和 git
        self.env = os.environ.copy()
        self.errors = []
        self.original_branch = None  # 记录原始分支,便于后面切回去

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
                self.log(f"✓ {command} 命令可用:{result.stdout.strip()}")
                return True
            else:
                self.log(f"✗ {command} 命令不可用,艹,检查一下你的环境变量!", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ 检查 {command} 命令时出错:{str(e)}", "ERROR")
            return False

    def run_command(self, command, cwd=None, description=""):
        """执行命令并实时输出"""
        self.log(f"执行:{description or command}")

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
                self.log(f"✗ {description or '命令'}执行失败,返回码:{return_code}", "ERROR")
                return False

        except Exception as e:
            self.log(f"✗ 执行命令出错:{str(e)}", "ERROR")
            return False

    def get_current_branch(self, cwd):
        """获取当前分支名"""
        try:
            result = subprocess.run(
                "git rev-parse --abbrev-ref HEAD",
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                env=self.env,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                self.log(f"当前分支:{branch}")
                return branch
            else:
                self.log(f"✗ 获取当前分支失败", "ERROR")
                return None
        except Exception as e:
            self.log(f"✗ 获取分支时出错:{str(e)}", "ERROR")
            return None

    def checkout_branch(self, branch_name, cwd):
        """切换分支"""
        return self.run_command(
            f"git checkout {branch_name}",
            cwd=cwd,
            description=f"切换到 {branch_name} 分支"
        )

    def pull_branch(self, cwd):
        """拉取当前分支最新代码"""
        return self.run_command(
            "git pull",
            cwd=cwd,
            description="拉取最新代码"
        )

    def merge_branch(self, branch_name, cwd):
        """合并指定分支到当前分支"""
        self.log(f"准备合并分支:{branch_name}")

        # 执行合并
        result = self.run_command(
            f"git merge {branch_name}",
            cwd=cwd,
            description=f"合并 {branch_name} 分支"
        )

        if not result:
            # 检查是否有冲突
            try:
                conflict_check = subprocess.run(
                    "git status",
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    env=self.env,
                    encoding='utf-8',
                    errors='ignore'
                )
                if "Unmerged paths" in conflict_check.stdout or "both modified" in conflict_check.stdout:
                    self.log("✗ 艹!检测到合并冲突,自动退出程序!", "ERROR")
                    self.log("手动解决冲突后再来运行吧!", "ERROR")
                    # 取消合并
                    subprocess.run("git merge --abort", shell=True, cwd=cwd, env=self.env)
                    return False
            except Exception as e:
                self.log(f"检查冲突状态时出错:{str(e)}", "ERROR")
                return False

        return result

    def handle_branch_merge(self):
        """处理分支合并流程"""
        self.log("=" * 60)
        self.log("准备进行分支合并操作")

        # 1. 获取当前分支
        self.original_branch = self.get_current_branch(PROJECT_DIR)
        if not self.original_branch:
            self.log("无法获取当前分支,艹!", "ERROR")
            return False

        # 2. 询问用户要合并的分支
        print("\n" + "-" * 60)
        merge_branch = input("请输入要合并的分支名称: ").strip()
        if not merge_branch:
            self.log("没有输入分支名称,跳过合并操作", "WARNING")
            return True

        self.log(f"用户输入的待合并分支:{merge_branch}")

        # 3. 切换到 待发布的 分支
        if not self.checkout_branch(merge_branch, PROJECT_DIR):
            self.log("切换到 待发布的 分支失败,艹!", "ERROR")
            return False

        # 4. 拉取 待发布的 分支最新代码
        if not self.pull_branch(PROJECT_DIR):
            self.log("拉取 待发布的 分支最新代码失败,艹!", "ERROR")
            return False

        # 3. 切换到 yufa 分支
        if not self.checkout_branch("yufa", PROJECT_DIR):
            self.log("切换到 yufa 分支失败,艹!", "ERROR")
            return False

        # 4. 拉取 yufa 分支最新代码
        if not self.pull_branch(PROJECT_DIR):
            self.log("拉取 yufa 分支最新代码失败,艹!", "ERROR")
            return False

        # 5. 合并用户指定的分支
        if not self.merge_branch(merge_branch, PROJECT_DIR):
            self.log(f"合并 {merge_branch} 分支失败,程序退出!", "ERROR")
            # 尝试切回原分支
            # self.checkout_branch(self.original_branch, PROJECT_DIR)
            return False

        self.log(f"✓ 成功合并 {merge_branch} 到 yufa 分支")
        return True

    def build_project(self):
        """先拉取 yufa-http 的最新代码"""
        # 执行 git pull
        self.run_command(
            "git pull",
            cwd=PROJECT_DIR,
            description="拉取 kf-manage-lite 最新代码"
        )
        
        """执行项目打包"""
        self.log("=" * 60)
        self.log("开始打包 kf-manage-lite 项目")

        # 检查项目目录
        if not os.path.exists(PROJECT_DIR):
            self.log(f"✗ 项目目录不存在:{PROJECT_DIR}", "ERROR")
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
            self.log(f"✗ staticDeploy 目录不存在:{STATIC_DEPLOY_DIR}", "ERROR")
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
            self.log(f"✗ 打包输出目录不存在:{BUILD_OUTPUT_DIR}", "ERROR")
            self.log("  可能是打包失败了,检查一下上面的错误信息", "ERROR")
            return False
        
        # 暂时不要，这个是可以复制到其他文件夹的，用户自定义的
        # # 2. 询问用户要复制的文件夹
        # print("\n" + "-" * 60)
        # copy_folder = input("请输入要复制的文件夹: ").strip()
        
        # DEPLOY_TARGET_DIR = os.path.join(STATIC_DEPLOY_DIR, copy_folder)
        
        try:
            # 如果目标目录存在,先删除
            if os.path.exists(DEPLOY_TARGET_DIR):
                self.log(f"删除旧的部署目录:{DEPLOY_TARGET_DIR}")
                shutil.rmtree(DEPLOY_TARGET_DIR)

            # 复制文件夹
            self.log(f"复制:{BUILD_OUTPUT_DIR}")
            self.log(f"  到:{DEPLOY_TARGET_DIR}")
            shutil.copytree(BUILD_OUTPUT_DIR, DEPLOY_TARGET_DIR)

            # 统计文件数量
            file_count = sum(1 for _ in Path(DEPLOY_TARGET_DIR).rglob("*") if _.is_file())
            self.log(f"✓ 复制完成,共 {file_count} 个文件")
            return True

        except Exception as e:
            self.log(f"✗ 复制文件时出错:{str(e)}", "ERROR")
            return False

    def run(self):
        """执行完整的打包部署流程"""
        print("\n" + "=" * 60)
        print("    开始操作 kf-manage-lite yufa-http  分支  这个发布的是 http")
        print("=" * 60 + "\n")

        # 1. 检查必要的命令
        self.log("检查环境...")
        if not self.check_command("bun"):
            self.log("艹,bun 都没装,还打包个锤子!", "ERROR")
            return False

        if not self.check_command("git"):
            self.log("git 也没有?你这环境太垃圾了!", "ERROR")
            return False


        # 3. 执行打包
        if not self.build_project():
            self.log("打包失败了,艹,检查一下代码有没有问题!", "ERROR")
            return False
        
        
        # 切换到 static 的 yufa 分支
        if not self.checkout_branch('yufa', STATIC_DEPLOY_DIR):
            self.log("切换到 static 的 yufa 分支失败,艹!", "ERROR")
            return False

        # 4. 更新 staticDeploy
        if not self.git_pull_static_deploy():
            self.log("git pull 失败,可能有冲突,手动处理一下吧", "WARNING")
            # 询问是否继续
            response = input("\n是否继续复制文件?(y/n): ")
            if response.lower() != 'y':
                self.log("用户取消操作")
                return False

        # 5. 复制打包产物
        if not self.copy_build_output():
            self.log("复制文件失败,艹,检查一下权限问题!", "ERROR")
            return False


        # 完成
        print("\n" + "=" * 60)
        self.log("🎉 所有操作完成!打包部署成功!", "SUCCESS")
        self.log(f"部署路径:{DEPLOY_TARGET_DIR}")
        print("=" * 60 + "\n")

        return True


def main():
    """主函数"""
    builder = AutoBuilder()

    try:
        success = builder.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断操作,艹,不玩了!")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n出现未知错误:{str(e)}")
        print("艹,这个错误老王也没见过,自己看着办吧!")
        sys.exit(1)


if __name__ == "__main__":
    main()
