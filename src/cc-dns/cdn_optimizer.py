#!/usr/bin/env python3
"""
CDN优化工具 - 自动选择最优CDN节点并更新hosts文件
支持 Windows, macOS, Linux
"""

import os
import sys
import platform
import subprocess
import socket
import time
import threading
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional
import tempfile
import shutil
from pathlib import Path

class CDNOptimizer:
    def __init__(self, domain: str, max_workers: int = 20):
        self.domain = domain.strip().lower()
        self.max_workers = max_workers
        self.system = platform.system().lower()
        self.hosts_file = self._get_hosts_file_path()
        self.backup_dir = Path.home() / '.cdn_optimizer_backups'
        self.backup_dir.mkdir(exist_ok=True)
        
        # 配置参数
        self.ping_count = 10  # ping测试次数
        self.timeout = 5      # 超时时间(秒)
        self.test_port = 80   # 测试端口
        
    def _get_hosts_file_path(self) -> str:
        """获取hosts文件路径"""
        if self.system == 'windows':
            return r'C:\Windows\System32\drivers\etc\hosts'
        else:  # macOS 和 Linux
            return '/etc/hosts'
    
    def _check_admin_privileges(self) -> bool:
        """检查管理员权限"""
        try:
            if self.system == 'windows':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.getuid() == 0
        except:
            return False
    
    def _require_admin(self):
        """要求管理员权限"""
        if not self._check_admin_privileges():
            print("❌ 错误: 需要管理员权限来修改hosts文件")
            if self.system == 'windows':
                print("请以管理员身份运行此脚本")
            else:
                print("请使用 sudo 运行此脚本")
            sys.exit(1)
    
    def resolve_cdn_ips(self) -> List[str]:
        """解析CDN的所有IP地址"""
        print(f"🔍 正在解析域名 {self.domain} 的IP地址...")
        
        ips = set()
        
        # 方法1: 使用socket.getaddrinfo
        try:
            result = socket.getaddrinfo(self.domain, None)
            for item in result:
                ip = item[4][0]
                if self._is_valid_ip(ip):
                    ips.add(ip)
        except Exception as e:
            print(f"⚠️  socket解析失败: {e}")
        
        # 方法2: 使用nslookup/dig命令
        try:
            if self.system == 'windows':
                cmd = ['nslookup', self.domain]
            else:
                cmd = ['dig', '+short', self.domain]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if self._is_valid_ip(line):
                        ips.add(line)
        except Exception as e:
            print(f"⚠️  命令行解析失败: {e}")
        
        # 方法3: 多次查询获取更多IP
        print("🔄 进行多次DNS查询以获取更多IP...")
        for i in range(10):
            try:
                result = socket.getaddrinfo(self.domain, None)
                for item in result:
                    ip = item[4][0]
                    if self._is_valid_ip(ip):
                        ips.add(ip)
                time.sleep(0.5)
            except:
                continue
        
        ip_list = list(ips)
        print(f"✅ 发现 {len(ip_list)} 个IP地址: {', '.join(ip_list)}")
        return ip_list
    
    def _is_valid_ip(self, ip: str) -> bool:
        """验证IP地址格式"""
        try:
            socket.inet_aton(ip)
            # 排除本地和保留地址
            parts = ip.split('.')
            if parts[0] in ['127', '0', '255']:
                return False
            if parts[0] == '10':
                return False
            if parts[0] == '172' and 16 <= int(parts[1]) <= 31:
                return False
            if parts[0] == '192' and parts[1] == '168':
                return False
            return True
        except:
            return False
    
    def ping_test(self, ip: str) -> Dict:
        """对单个IP进行ping测试"""
        try:
            if self.system == 'windows':
                cmd = ['ping', '-n', str(self.ping_count), '-w', str(self.timeout * 1000), ip]
            else:
                cmd = ['ping', '-c', str(self.ping_count), '-W', str(self.timeout), ip]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            end_time = time.time()
            
            if result.returncode == 0:
                # 解析ping结果
                output = result.stdout
                avg_time = self._parse_ping_result(output)
                
                return {
                    'ip': ip,
                    'success': True,
                    'avg_time': avg_time,
                    'total_time': end_time - start_time,
                    'packet_loss': 0
                }
            else:
                return {
                    'ip': ip,
                    'success': False,
                    'avg_time': float('inf'),
                    'total_time': end_time - start_time,
                    'packet_loss': 100
                }
                
        except subprocess.TimeoutExpired:
            return {
                'ip': ip,
                'success': False,
                'avg_time': float('inf'),
                'total_time': 30,
                'packet_loss': 100
            }
        except Exception as e:
            return {
                'ip': ip,
                'success': False,
                'avg_time': float('inf'),
                'total_time': 0,
                'packet_loss': 100,
                'error': str(e)
            }
    
    def _parse_ping_result(self, output: str) -> float:
        """解析ping命令的输出，提取平均延迟"""
        try:
            if self.system == 'windows':
                # Windows ping输出解析
                lines = output.split('\n')
                for line in lines:
                    if '平均' in line or 'Average' in line:
                        # 提取数字
                        import re
                        numbers = re.findall(r'\d+', line)
                        if numbers:
                            return float(numbers[-1])
            else:
                # Linux/macOS ping输出解析
                lines = output.split('\n')
                for line in lines:
                    if 'avg' in line or 'min/avg/max' in line:
                        import re
                        # 匹配 min/avg/max/stddev = 1.234/5.678/9.012/1.345 ms
                        match = re.search(r'[\d.]+/([\d.]+)/[\d.]+', line)
                        if match:
                            return float(match.group(1))
            
            # 如果无法解析平均值，返回一个较大的值
            return 1000.0
        except:
            return 1000.0
    
    def tcp_test(self, ip: str) -> Dict:
        """TCP连接测试"""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, self.test_port))
            end_time = time.time()
            sock.close()
            
            if result == 0:
                return {
                    'ip': ip,
                    'success': True,
                    'connect_time': (end_time - start_time) * 1000,  # 转换为毫秒
                }
            else:
                return {
                    'ip': ip,
                    'success': False,
                    'connect_time': float('inf'),
                }
        except Exception as e:
            return {
                'ip': ip,
                'success': False,
                'connect_time': float('inf'),
                'error': str(e)
            }
    
    def comprehensive_test(self, ips: List[str]) -> List[Dict]:
        """对所有IP进行综合测试"""
        print(f"🚀 开始测试 {len(ips)} 个IP地址...")
        print(f"📊 测试参数: ping次数={self.ping_count}, 超时={self.timeout}s, 并发数={self.max_workers}")
        
        results = []
        
        # 使用线程池并发测试
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交ping测试任务
            ping_futures = {executor.submit(self.ping_test, ip): ip for ip in ips}
            tcp_futures = {executor.submit(self.tcp_test, ip): ip for ip in ips}
            
            ping_results = {}
            tcp_results = {}
            
            # 收集ping测试结果
            for future in as_completed(ping_futures):
                ip = ping_futures[future]
                try:
                    result = future.result()
                    ping_results[ip] = result
                    status = "✅" if result['success'] else "❌"
                    print(f"{status} {ip}: ping={result['avg_time']:.1f}ms")
                except Exception as e:
                    ping_results[ip] = {'ip': ip, 'success': False, 'error': str(e)}
                    print(f"❌ {ip}: ping测试失败 - {e}")
            
            # 收集TCP测试结果
            for future in as_completed(tcp_futures):
                ip = tcp_futures[future]
                try:
                    result = future.result()
                    tcp_results[ip] = result
                except Exception as e:
                    tcp_results[ip] = {'ip': ip, 'success': False, 'error': str(e)}
        
        # 合并结果
        for ip in ips:
            ping_data = ping_results.get(ip, {})
            tcp_data = tcp_results.get(ip, {})
            
            combined = {
                'ip': ip,
                'ping_success': ping_data.get('success', False),
                'ping_avg': ping_data.get('avg_time', float('inf')),
                'tcp_success': tcp_data.get('success', False),
                'tcp_time': tcp_data.get('connect_time', float('inf')),
                'score': 0
            }
            
            # 计算综合评分 (越低越好)
            if combined['ping_success'] and combined['tcp_success']:
                combined['score'] = combined['ping_avg'] + combined['tcp_time'] * 0.1
            elif combined['ping_success']:
                combined['score'] = combined['ping_avg'] + 1000
            else:
                combined['score'] = float('inf')
            
            results.append(combined)
        
        # 按评分排序
        results.sort(key=lambda x: x['score'])
        return results
    
    def backup_hosts_file(self) -> str:
        """备份hosts文件"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"hosts_backup_{timestamp}.txt"
        
        try:
            shutil.copy2(self.hosts_file, backup_file)
            print(f"📋 已备份hosts文件到: {backup_file}")
            return str(backup_file)
        except Exception as e:
            print(f"⚠️  备份hosts文件失败: {e}")
            return ""
    
    def update_hosts_file(self, best_ip: str) -> bool:
        """更新hosts文件"""
        try:
            # 读取当前hosts文件
            with open(self.hosts_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 移除旧的域名条目
            new_lines = []
            for line in lines:
                line_clean = line.strip()
                if line_clean and not line_clean.startswith('#'):
                    parts = line_clean.split()
                    if len(parts) >= 2 and parts[1] == self.domain:
                        continue  # 跳过旧条目
                new_lines.append(line)
            
            # 添加新条目
            new_lines.append(f"\n# CDN Optimizer - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            new_lines.append(f"{best_ip} {self.domain}\n")
            
            # 写入hosts文件
            with open(self.hosts_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            print(f"✅ 已更新hosts文件: {best_ip} -> {self.domain}")
            return True
            
        except Exception as e:
            print(f"❌ 更新hosts文件失败: {e}")
            return False
    
    def flush_dns(self):
        """刷新DNS缓存"""
        print("🔄 刷新DNS缓存...")
        try:
            if self.system == 'windows':
                subprocess.run(['ipconfig', '/flushdns'], check=True)
            elif self.system == 'darwin':  # macOS
                subprocess.run(['sudo', 'dscacheutil', '-flushcache'], check=True)
                subprocess.run(['sudo', 'killall', '-HUP', 'mDNSResponder'], check=True)
            else:  # Linux
                # 尝试多种DNS缓存刷新方法
                commands = [
                    ['systemctl', 'restart', 'systemd-resolved'],
                    ['service', 'nscd', 'restart'],
                    ['service', 'dnsmasq', 'restart']
                ]
                for cmd in commands:
                    try:
                        subprocess.run(cmd, check=True, timeout=10)
                        break
                    except:
                        continue
            print("✅ DNS缓存已刷新")
        except Exception as e:
            print(f"⚠️  DNS缓存刷新失败: {e}")
    
    def print_results(self, results: List[Dict]):
        """打印测试结果"""
        print("\n" + "="*80)
        print("📊 测试结果汇总")
        print("="*80)
        print(f"{'排名':<4} {'IP地址':<16} {'Ping延迟':<12} {'TCP连接':<12} {'综合评分':<12} {'状态'}")
        print("-"*80)
        
        for i, result in enumerate(results, 1):  # 显示所有结果
            ping_status = f"{result['ping_avg']:.1f}ms" if result['ping_success'] else "失败"
            tcp_status = f"{result['tcp_time']:.1f}ms" if result['tcp_success'] else "失败"
            score = f"{result['score']:.1f}" if result['score'] != float('inf') else "∞"
            status = "🟢 优秀" if result['score'] < 100 else "🟡 良好" if result['score'] < 300 else "🔴 较差"
            
            print(f"{i:<4} {result['ip']:<16} {ping_status:<12} {tcp_status:<12} {score:<12} {status}")
    
    def save_results(self, results: List[Dict], filename: str = None):
        """保存测试结果到文件"""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"cdn_test_results_{self.domain}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'domain': self.domain,
                    'test_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'system': platform.system(),
                    'results': results
                }, f, indent=2, ensure_ascii=False)
            print(f"💾 测试结果已保存到: {filename}")
        except Exception as e:
            print(f"⚠️  保存结果失败: {e}")
    
    def run(self, update_hosts: bool = True, save_results: bool = True) -> Optional[str]:
        """运行CDN优化流程"""
        try:
            print("🚀 CDN优化工具启动")
            print(f"🌐 目标域名: {self.domain}")
            print(f"💻 系统平台: {platform.system()} {platform.release()}")
            
            # 解析CDN IP地址
            ips = self.resolve_cdn_ips()
            if not ips:
                print("❌ 未能解析到任何IP地址")
                return None
            
            # 进行综合测试
            results = self.comprehensive_test(ips)
            
            # 打印结果
            self.print_results(results)
            
            # 保存结果
            if save_results:
                self.save_results(results)
            
            # 找到最优IP
            best_result = None
            for result in results:
                if result['ping_success'] and result['tcp_success']:
                    best_result = result
                    break
            
            if not best_result:
                print("❌ 未找到可用的IP地址")
                return None
            
            best_ip = best_result['ip']
            print(f"\n🏆 最优IP: {best_ip}")
            print(f"   Ping延迟: {best_result['ping_avg']:.1f}ms")
            print(f"   TCP连接: {best_result['tcp_time']:.1f}ms")
            print(f"   综合评分: {best_result['score']:.1f}")
            
            # 更新hosts文件
            if update_hosts:
                self._require_admin()
                self.backup_hosts_file()
                if self.update_hosts_file(best_ip):
                    self.flush_dns()
                    print(f"✅ CDN优化完成! 域名 {self.domain} 现在指向最优IP {best_ip}")
                else:
                    print("❌ hosts文件更新失败")
                    return None
            
            return best_ip
            
        except KeyboardInterrupt:
            print("\n⏹️  用户中断操作")
            return None
        except Exception as e:
            print(f"❌ 运行出错: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='CDN优化工具 - 自动选择最优CDN节点')
    parser.add_argument('domain', help='要优化的域名')
    parser.add_argument('-w', '--workers', type=int, default=20, help='并发线程数 (默认: 20)')
    parser.add_argument('-c', '--count', type=int, default=10, help='ping测试次数 (默认: 10)')
    parser.add_argument('-t', '--timeout', type=int, default=5, help='超时时间(秒) (默认: 5)')
    parser.add_argument('--no-update', action='store_true', help='不更新hosts文件，仅测试')
    parser.add_argument('--no-save', action='store_true', help='不保存测试结果')
    
    args = parser.parse_args()
    
    # 创建优化器
    optimizer = CDNOptimizer(args.domain, args.workers)
    optimizer.ping_count = args.count
    optimizer.timeout = args.timeout
    
    # 运行优化
    result = optimizer.run(
        update_hosts=not args.no_update,
        save_results=not args.no_save
    )
    
    if result:
        print(f"\n🎉 优化成功! 最优IP: {result}")
        sys.exit(0)
    else:
        print("\n💔 优化失败")
        sys.exit(1)

if __name__ == '__main__':
    main()