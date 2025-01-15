import psutil

def get_running_processes():
    # 获取当前运行的进程信息
    return [p.info for p in psutil.process_iter(['pid', 'name', 'username'])]

def kill_process_by_name(process_name):
    # 遍历当前运行的进程
    for p in psutil.process_iter(['pid', 'name', 'username']):
        # 如果进程名匹配，则终止进程
        if p.info['name'] == process_name:
            p.kill()

# 获取运行中的进程列表
running_processes = get_running_processes()
print('found %d running processes' % len(running_processes))

# 杀死指定名称的进程（请谨慎使用）
# kill_process_by_name('process_name_here')