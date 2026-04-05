#!/usr/bin/env python3
"""
定时调度器 — 检测触发条件，发派任务到终端
只做检测和发派，调度逻辑由编译时确定。
"""

import json
import time
import subprocess
import datetime
import os
import sys

MANIFEST = 'task-manifest.json'


def load_manifest():
    with open(MANIFEST, 'r') as f:
        return json.load(f)['tasks']


def save_manifest(tasks):
    with open(MANIFEST, 'r') as f:
        data = json.load(f)
    data['tasks'] = tasks
    with open(MANIFEST, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_task_config(task):
    """只返回该任务的配置，不暴露其他任务信息"""
    return json.dumps(task, ensure_ascii=False)


def compile_dispatch_command(task):
    """将任务配置编译为 Claude 命令"""
    config = get_task_config(task)
    instruction = task['task']['instruction']
    skills = ', '.join(task['task'].get('skills', []))
    delivery_path = task['delivery']['path']
    log_path = task['delivery']['log_path']
    timeout = task['task'].get('timeout', 3600)

    prompt = (
        f"你正在执行一个自动化任务。\\n\\n"
        f"任务配置：\\n```json\\n{config}\\n```\\n\\n"
        f"请按照配置执行：\\n"
        f"1. 验证环境依赖（env vars、tools、files）\\n"
        f"2. 执行: {instruction}\\n"
        f"3. 结果写入: {delivery_path}\\n"
        f"4. 将执行结果以 JSONL 格式追加到: {log_path}\\n"
        f"5. 如需使用的 skills: {skills}\\n"
        f"6. 完成后退出终端\\n"
    )

    # Escape for AppleScript
    escaped = prompt.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    return f'claude --permission-mode bypassPermissions --print "{escaped}"'


def dispatch(task):
    """打开终端，发派任务"""
    command = compile_dispatch_command(task)

    # macOS: open Terminal via osascript, close on completion
    if sys.platform == 'darwin':
        escaped_cmd = command.replace('\\', '\\\\').replace('"', '\\"')
        # do script returns a tab reference; close that tab when command is done
        script = (
            f'tell application "Terminal" to activate\n'
            f'set newTab to do script "{escaped_cmd}"\n'
            f'delay 0.5\n'
            f'repeat while busy of newTab\n'
            f'  delay 1\n'
            f'end repeat\n'
            f'close newTab'
        )
        subprocess.Popen(['osascript', '-e', script])
    # Windows: open cmd window, close on completion (/c = run then close)
    elif sys.platform == 'win32':
        subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/c', command], shell=False)
    # Linux: use gnome-terminal, close on completion
    else:
        subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'{command}; exit'])

    return True


def check_schedule():
    """检查定时触发"""
    tasks = load_manifest()
    now = datetime.datetime.now().strftime("%H:%M")
    today = datetime.date.today().isoformat()

    for task in tasks:
        if task['status'] != 'active':
            continue
        if task['trigger']['type'] != 'schedule':
            continue
        if task['trigger']['time'] != now:
            continue

        # 检查今天是否已执行
        last_run = task.get('last_run', '')
        if last_run and last_run.startswith(today):
            continue

        print(f"[{now}] 发派任务: {task['name']} ({task['id']})")
        if dispatch(task):
            task['last_run'] = datetime.datetime.now().isoformat()
            task['run_count'] = task.get('run_count', 0) + 1
            save_manifest(tasks)


def list_tasks():
    """列出所有任务"""
    tasks = load_manifest()
    print(f"\n{'ID':<20} {'Name':<20} {'Trigger':<15} {'Status':<10} {'Last Run':<20}")
    print('-' * 85)
    for t in tasks:
        trigger = t['trigger']['type']
        if trigger == 'schedule':
            trigger += f" @{t['trigger']['time']}"
        last_run = t.get('last_run', 'never') or 'never'
        print(f"{t['id']:<20} {t['name']:<20} {trigger:<15} {t['status']:<10} {last_run:<20}")


def run_once(task_id):
    """手动触发单个任务"""
    tasks = load_manifest()
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        print(f"Task not found: {task_id}")
        return

    print(f"手动触发: {task['name']} ({task['id']})")
    if dispatch(task):
        task['last_run'] = datetime.datetime.now().isoformat()
        task['run_count'] = task.get('run_count', 0) + 1
        save_manifest(tasks)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'list':
            list_tasks()
        elif cmd == 'run' and len(sys.argv) > 2:
            run_once(sys.argv[2])
        else:
            print("Usage:")
            print("  dispatch.py              # Start scheduler loop")
            print("  dispatch.py list         # List all tasks")
            print("  dispatch.py run <id>     # Trigger a task manually")
    else:
        print("定时调度器运行中... (Ctrl+C 退出)")
        print("每分钟检查一次触发条件\n")
        try:
            while True:
                check_schedule()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n调度器已停止")
