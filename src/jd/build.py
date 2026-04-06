#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多项目自动化打包部署工具
从 config.yaml 读取配置，支持终端上下键选择项目。
依赖: pip install pyyaml inquirer
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time
import yaml
import inquirer

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

def load_config():
    """加载并校验 YAML 配置"""
    if not os.path.exists(CONFIG_FILE):
        print(f"✗ 找不到配置文件: {CONFIG_FILE}")
        print("请创建 config.yaml 并参考示例配置项目信息。")
        sys.exit(1)
        
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        projects = data.get("projects", [])
        if not projects:
            print("✗ 配置文件中没有找到 'projects' 配置项。")
            sys.exit(1)
        return projects
    except yaml.YAMLError as e:
        print(f"✗ YAML 解析失败: {e}")
        sys.exit(1)

def select_project(projects):
    """终端上下箭头选择项目"""
    questions = [
        inquirer.List(
            'project',
            message="请选择要操作的项目 (↑↓ 选择, Enter 确认)",
            choices=[p['name'] for p in projects],
            carousel=True
        ),
    ]
    answers = inquirer.prompt(questions)
    if not answers:
        print("\n用户取消选择，退出。")
        sys.exit(0)
        
    selected_name = answers['project']
    return next(p for p in projects if p['name'] == selected_name)


class AutoBuilder:
    """自动化构建部署类"""

    def __init__(self, config):
        self.config = config
        self.env = os.environ.copy()
        self.original_branch = None
        
        # 路径处理：支持相对路径和绝对路径
        self.project_dir = self.config['project_dir']
        self.static_deploy_dir = self.config['static_deploy_dir']
        
        self.build_output_dir = self.config['build_output_dir']
        if not os.path.isabs(self.build_output_dir):
            self.build_output_dir = os.path.join(self.project_dir, self.build_output_dir)
            
        self.deploy_target_dir = self.config['deploy_target_dir']
        if not os.path.isabs(self.deploy_target_dir):
            self.deploy_target_dir = os.path.join(self.static_deploy_dir, self.deploy_target_dir)
            
        # 分支与命令配置
        self.deploy_target_branch = self.config.get('deploy_target_branch', 'yufa-http')
        self.static_repo_branch = self.config.get('static_repo_branch', 'yufa')
        self.build_command = self.config.get('build_command', 'bun build')

    def log(self, message, level="INFO"):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def check_command(self, command):
        cmd = f"where {command}" if sys.platform == "win32" else f"which {command}"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=self.env)
            if result.returncode == 0:
                self.log(f"✓ {command} 命令可用: {result.stdout.strip()}")
                return True
            else:
                self.log(f"✗ {command} 命令不可用, 艹, 检查一下你的环境变量!", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ 检查 {command} 命令时出错: {str(e)}", "ERROR")
            return False

    def run_command(self, command, cwd=None, description=""):
        self.log(f"执行: {description or command}")
        try:
            process = subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, cwd=cwd, env=self.env, encoding='utf-8', errors='ignore'
            )
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(f"  > {line.rstrip()}")
            return_code = process.wait()
            if return_code == 0:
                self.log(f"✓ {description or '命令'} 执行成功")
                return True
            else:
                self.log(f"✗ {description or '命令'} 执行失败, 返回码: {return_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ 执行命令出错: {str(e)}", "ERROR")
            return False

    def get_current_branch(self, cwd):
        try:
            result = subprocess.run(
                "git rev-parse --abbrev-ref HEAD", shell=True, capture_output=True, text=True,
                cwd=cwd, env=self.env, encoding='utf-8', errors='ignore'
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                self.log(f"当前分支: {branch}")
                return branch
            self.log("✗ 获取当前分支失败", "ERROR")
            return None
        except Exception as e:
            self.log(f"✗ 获取分支时出错: {str(e)}", "ERROR")
            return None

    def checkout_branch(self, branch_name, cwd):
        return self.run_command(f"git checkout {branch_name}", cwd=cwd, description=f"切换到 {branch_name} 分支")

    def pull_branch(self, cwd):
        return self.run_command("git pull", cwd=cwd, description="拉取最新代码")

    def merge_branch(self, branch_name, cwd):
        self.log(f"准备合并分支: {branch_name}")
        result = self.run_command(f"git merge {branch_name}", cwd=cwd, description=f"合并 {branch_name} 分支")
        if not result:
            try:
                status = subprocess.run("git status", shell=True, capture_output=True, text=True, cwd=cwd, env=self.env, encoding='utf-8', errors='ignore')
                if "Unmerged paths" in status.stdout or "both modified" in status.stdout:
                    self.log("✗ 艹! 检测到合并冲突, 自动退出程序!", "ERROR")
                    self.log("手动解决冲突后再来运行吧!", "ERROR")
                    subprocess.run("git merge --abort", shell=True, cwd=cwd, env=self.env)
                    return False
            except Exception as e:
                self.log(f"检查冲突状态时出错: {str(e)}", "ERROR")
        return result

    def handle_branch_merge(self):
        self.log("=" * 60)
        self.log("准备进行分支合并操作")
        
        self.original_branch = self.get_current_branch(self.project_dir)
        if not self.original_branch:
            self.log("无法获取当前分支, 艹!", "ERROR")
            return False

        print("\n" + "-" * 60)
        merge_branch = input("请输入要合并的【开发分支】名称 (留空跳过): ").strip()
        if not merge_branch:
            self.log("没有输入分支名称, 跳过合并操作", "WARNING")
            return True

        self.log(f"用户输入的待合并分支: {merge_branch}")
        
        if not self.checkout_branch(merge_branch, self.project_dir):
            self.log("切换到待发布分支失败, 艹!", "ERROR"); return False
        if not self.pull_branch(self.project_dir):
            self.log("拉取待发布分支最新代码失败, 艹!", "ERROR"); return False
        if not self.checkout_branch(self.deploy_target_branch, self.project_dir):
            self.log(f"切换到 {self.deploy_target_branch} 分支失败, 艹!", "ERROR"); return False
        if not self.pull_branch(self.project_dir):
            self.log(f"拉取 {self.deploy_target_branch} 分支最新代码失败, 艹!", "ERROR"); return False
        if not self.merge_branch(merge_branch, self.project_dir):
            self.log(f"合并 {merge_branch} 分支失败, 程序退出!", "ERROR"); return False

        self.log(f"✓ 成功合并 {merge_branch} 到 {self.deploy_target_branch} 分支")
        return True

    def build_project(self):
        self.log("=" * 60)
        self.log(f"开始打包项目: {self.config['name']}")
        if not os.path.exists(self.project_dir):
            self.log(f"✗ 项目目录不存在: {self.project_dir}", "ERROR"); return False
        return self.run_command(self.build_command, cwd=self.project_dir, description=f"执行 {self.build_command} 打包命令")

    def git_pull_static_deploy(self):
        self.log("=" * 60)
        self.log("更新 staticDeploy 仓库")
        if not os.path.exists(self.static_deploy_dir):
            self.log(f"✗ staticDeploy 目录不存在: {self.static_deploy_dir}", "ERROR"); return False
        return self.run_command("git pull", cwd=self.static_deploy_dir, description="拉取 staticDeploy 最新代码")

    def copy_build_output(self):
        self.log("=" * 60)
        self.log("复制打包产物到部署目录")
        if not os.path.exists(self.build_output_dir):
            self.log(f"✗ 打包输出目录不存在: {self.build_output_dir}", "ERROR")
            self.log("  可能是打包失败了, 检查一下上面的错误信息", "ERROR"); return False
        try:
            if os.path.exists(self.deploy_target_dir):
                self.log(f"删除旧的部署目录: {self.deploy_target_dir}")
                shutil.rmtree(self.deploy_target_dir)
            self.log(f"复制: {self.build_output_dir}")
            self.log(f"  到: {self.deploy_target_dir}")
            shutil.copytree(self.build_output_dir, self.deploy_target_dir)
            file_count = sum(1 for _ in Path(self.deploy_target_dir).rglob("*") if _.is_file())
            self.log(f"✓ 复制完成, 共 {file_count} 个文件")
            return True
        except Exception as e:
            self.log(f"✗ 复制文件时出错: {str(e)}", "ERROR"); return False

    # =====================================================

    def run(self):
        print("\n" + "=" * 60)
        print(f"    项目: {self.config['name']} | 操作分支: {self.deploy_target_branch}")
        print("=" * 60 + "\n")

        # 1. 环境检查
        required_cmd = "bun" if "bun" in self.build_command else "npm"
        if not self.check_command("git") or not self.check_command(required_cmd):
            self.log("环境检查失败, 艹, 连基础命令都没有还打包个锤子!", "ERROR"); return False

        # 2. 分支合并
        if not self.handle_branch_merge():
            self.log("分支合并失败, 程序退出!", "ERROR"); return False

        # 3. 执行打包
        if not self.build_project():
            self.log("打包失败了, 艹, 检查一下代码有没有问题!", "ERROR"); return False
        
        # 4. 切换 static 仓库分支并拉取
        if not self.checkout_branch(self.static_repo_branch, self.static_deploy_dir):
            self.log(f"切换到 static 的 {self.static_repo_branch} 分支失败, 艹!", "ERROR"); return False
        if not self.git_pull_static_deploy():
            self.log("git pull 失败, 可能有冲突, 手动处理一下吧", "WARNING")
            if input("\n是否继续复制文件? (y/n): ").lower() != 'y':
                self.log("用户取消操作"); return False

        # 5. 复制打包产物
        if not self.copy_build_output():
            self.log("复制文件失败, 艹, 检查一下权限问题!", "ERROR"); return False

        # 7. 切回原始分支
        if self.original_branch:
            self.log("=" * 60)
            self.log(f"切回原始分支: {self.original_branch}")
            if not self.checkout_branch(self.original_branch, self.project_dir):
                self.log(f"切回 {self.original_branch} 分支失败, 需要手动切换!", "WARNING")

        # 完成
        print("\n" + "=" * 60)
        self.log("🎉 所有操作完成! 打包部署成功!", "SUCCESS")
        self.log(f"部署路径: {self.deploy_target_dir}")
        self.log("💡 文件已自动添加到暂存区，请手动检查后执行 git commit")
        print("=" * 60 + "\n")
        return True


def main():
    projects = load_config()
    selected_config = select_project(projects)
    
    builder = AutoBuilder(selected_config)
    try:
        success = builder.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断操作, 艹, 不玩了!")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n出现未知错误: {str(e)}")
        print("艹, 这个错误老王也没见过, 自己看着办吧!")
        sys.exit(1)

if __name__ == "__main__":
    main()
