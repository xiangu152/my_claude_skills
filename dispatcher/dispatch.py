#!/usr/bin/env python3
"""
调度器 — 检测触发条件，发派任务到终端
调度逻辑由编译时生成的 trigger 函数决定，调度器只负责调用。
"""

import json
import time
import subprocess
import datetime
import os
import sys

BASE_DIR = os.path.expanduser('~/.claude')
MANIFEST = os.path.join(BASE_DIR, 'task-manifest.json')
TASK_DISPATCH_DIR = os.path.join(BASE_DIR, 'dispatcher/_dispatched')


def _get_shell_rc_paths():
    """返回当前平台可能存在的 shell 配置文件路径"""
    candidates = [
        '~/.zshrc',
        '~/.bashrc',
        '~/.bash_profile',
        '~/.profile',
    ]
    if sys.platform == 'win32':
        # Windows: 环境变量通常通过系统设置，不依赖 shell rc
        return []
    return [os.path.expanduser(p) for p in candidates]


def load_shell_env():
    """从 shell 配置文件读取任务所需的环境变量，注入到 os.environ"""
    required_keys = set()
    tasks = load_manifest()
    for t in tasks:
        for var in t.get('environment', {}).get('env_vars', []):
            required_keys.add(var)

    if not required_keys:
        return

    for rc_path in _get_shell_rc_paths():
        try:
            with open(rc_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('export ') and '=' in line:
                        rest = line[len('export '):]
                        key, _, val = rest.partition('=')
                        key = key.strip()
                        if key in required_keys and key not in os.environ:
                            val = val.strip().strip('"').strip("'")
                            os.environ[key] = val
        except Exception:
            continue


def load_manifest():
    with open(MANIFEST, 'r') as f:
        return json.load(f)['tasks']


def save_manifest(tasks):
    with open(MANIFEST, 'r') as f:
        data = json.load(f)
    data['tasks'] = tasks
    with open(MANIFEST, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_dispatch_file(task):
    """将任务说明写入清单文件，返回文件路径"""
    os.makedirs(TASK_DISPATCH_DIR, exist_ok=True)
    task_id = task['id']
    file_path = os.path.join(TASK_DISPATCH_DIR, f'{task_id}.json')

    config = json.dumps(task, ensure_ascii=False, indent=2)
    instruction = task['task']['instruction']
    skills = ', '.join(task['task'].get('skills', []))
    delivery_path = task['delivery']['path']
    log_path = task['delivery']['log_path']

    # 编译时打包所需的环境变量信息（仅用于 Claude 参考）
    env_vars = task.get('environment', {}).get('env_vars', [])
    env_block = ""
    if env_vars:
        env_lines = []
        for var in env_vars:
            val = os.environ.get(var, '')
            status = "已注入" if val else "缺失"
            env_lines.append(f'- {var}: {status}')
        env_block = "### 环境变量\n" + "\n".join(env_lines) + "\n\n"

    content = (
        f"你正在执行一个自动化任务。\n\n"
        f"{env_block}"
        f"任务配置：\n```json\n{config}\n```\n\n"
        f"请按照配置执行：\n"
        f"1. 验证环境依赖（env vars、tools、files）\n"
        f"2. 执行: {instruction}\n"
        f"3. 结果写入: {delivery_path}\n"
        f"4. 将执行结果以 JSONL 格式追加到: {log_path}\n"
        f"5. 如需使用的 skills: {skills}\n"
        f"6. 完成后退出终端\n"
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return file_path


def compile_dispatch_command(task):
    """通过清单文件生成 Claude 命令，避免命令行参数截断"""
    dispatch_file = write_dispatch_file(task)

    # 编译时从当前环境捕获所需的环境变量，注入到子进程
    env_exports = []
    for var in task.get('environment', {}).get('env_vars', []):
        val = os.environ.get(var, '')
        if val:
            env_exports.append(f'export {var}="{val}"')

    env_prefix = "; ".join(env_exports) + "; " if env_exports else ""
    claude_cmd = f"{env_prefix}claude --permission-mode bypassPermissions --print \"$(cat '{dispatch_file}')\""

    if sys.platform == 'darwin':
        close_window = """osascript -e 'tell application "Terminal" to close front window'"""
        return f"{claude_cmd}; {close_window}"
    elif sys.platform == 'win32':
        return f"{claude_cmd} && exit"
    else:
        return f"{claude_cmd}; exit"


SKILL_DIR = os.path.expanduser('~/.claude/skills')


def verify_task(task):
    """编译时验证任务的环境依赖（Phase 2 + Phase 4）"""
    errors = []
    warnings = []

    # 1. 检查环境变量
    for var in task.get('environment', {}).get('env_vars', []):
        if not os.environ.get(var):
            errors.append(f"环境变量 {var} 未设置")

    # 2. 检查工具
    for tool in task.get('environment', {}).get('tools', []):
        which_cmd = ['where' if sys.platform == 'win32' else 'which', tool]
        result = subprocess.run(which_cmd, capture_output=True)
        if result.returncode != 0:
            errors.append(f"工具 {tool} 未找到")

    # 3. 检查文件/目录
    for f in task.get('environment', {}).get('files', []):
        f_expanded = os.path.expanduser(f)
        if not os.path.exists(f_expanded):
            errors.append(f"路径 {f} 不存在")

    # 4. 检查 skills
    for skill_name in task['task'].get('skills', []):
        skill_path = os.path.join(SKILL_DIR, skill_name)
        if not os.path.isdir(skill_path):
            errors.append(f"Skill {skill_name} 目录不存在: {skill_path}")
            continue
        # 检查 skill 的脚本是否存在
        skill_md = os.path.join(skill_path, 'SKILL.md')
        if os.path.isfile(skill_md):
            with open(skill_md, 'r') as f:
                content = f.read()
            # 提取 scripts/ 引用的文件
            import re
            for m in re.finditer(r'scripts/\S+\.m?js', content):
                script_rel = m.group(0)
                script_abs = os.path.join(skill_path, script_rel)
                if not os.path.isfile(script_abs):
                    errors.append(f"Skill {skill_name} 脚本不存在: {script_rel}")

    return errors, warnings


def test_run_task(task):
    """编译时试跑：用 claude --print 执行一次，验证输出和日志"""
    print(f"  试跑中...")
    command = compile_dispatch_command(task)

    delivery_path = os.path.expanduser(task['delivery']['path'])
    log_path = os.path.expanduser(task['delivery']['log_path'])

    # 备份已有文件
    backup = None
    if os.path.exists(delivery_path):
        backup = delivery_path + '.bak'
        os.rename(delivery_path, backup)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=task['task'].get('timeout', 300)
        )

        # 检查输出文件
        if not os.path.exists(delivery_path):
            return False, f"试跑失败: 输出文件 {delivery_path} 未生成"

        # 检查日志文件
        if not os.path.exists(log_path):
            return False, f"试跑失败: 日志文件 {log_path} 未生成"

        # 检查日志最后一条是否 success
        with open(log_path, 'r') as f:
            lines = [l.strip() for l in f if l.strip()]
        if lines:
            last_entry = json.loads(lines[-1])
            if last_entry.get('status') not in ('success', 'partial'):
                return False, f"试跑失败: 日志状态为 {last_entry.get('status')}"

        return True, "试跑通过"

    except subprocess.TimeoutExpired:
        return False, "试跑超时"
    finally:
        # 恢复备份
        if backup and os.path.exists(backup):
            os.rename(backup, delivery_path)


def compile_task(task_id):
    """编译任务：验证环境 -> 写入清单 -> 试跑 -> 注册"""
    tasks = load_manifest()
    existing = next((t for t in tasks if t['id'] == task_id), None)

    if existing:
        task = existing
        print(f"更新任务: {task['name']} ({task_id})")
    else:
        print(f"错误: 任务 {task_id} 未在 task-manifest.json 中定义")
        print(f"请先在 task-manifest.json 中添加任务配置，然后运行 compile")
        return False

    # Phase 2: 环境验证
    print(f"\n[Phase 2] 环境验证...")
    errors, warnings = verify_task(task)
    for w in warnings:
        print(f"  ⚠ {w}")
    if errors:
        for e in errors:
            print(f"  ✗ {e}")
        print(f"\n环境验证失败，共 {len(errors)} 个错误。请修复后重试。")
        return False
    print(f"  ✓ 环境验证通过")

    # Phase 3: 打包任务
    print(f"\n[Phase 3] 打包任务...")
    dispatch_file = write_dispatch_file(task)
    print(f"  ✓ 清单文件: {dispatch_file}")

    # Phase 4: 试跑
    print(f"\n[Phase 4] 试跑...")
    ok, msg = test_run_task(task)
    if not ok:
        print(f"  ✗ {msg}")
        return False
    print(f"  ✓ {msg}")

    # Phase 5: 注册
    print(f"\n[Phase 5] 注册任务...")
    task['compiled_at'] = datetime.datetime.now().isoformat()
    save_manifest(tasks)
    print(f"  ✓ 任务 {task_id} 编译完成并注册")
    return True


def dispatch(task):
    """发派任务到子进程执行（弹出终端窗口）"""
    command = compile_dispatch_command(task)

    # dispatch.py 所在目录，确保 cat 能找到清单文件
    project_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(project_root)  # dispatcher/ -> 项目根

    full_command = f'cd {project_root} && {command}'

    if sys.platform == 'darwin':
        # macOS: 通过 AppleScript 打开 Terminal
        escaped = full_command.replace('\\', '\\\\').replace('"', '\\"')
        applescript = (
            f'tell application "Terminal"\n'
            f'  activate\n'
            f'  do script "{escaped}"\n'
            f'end tell'
        )
        subprocess.run(['osascript', '-e', applescript], capture_output=True)
    elif sys.platform == 'win32':
        # Windows: 打开新 cmd 窗口
        subprocess.run(f'start cmd /c "{full_command}"', shell=True)
    else:
        # Linux: 尝试 gnome-terminal, 回退 xterm
        try:
            subprocess.run(
                ['gnome-terminal', '--', 'bash', '-c', full_command],
                capture_output=True
            )
        except FileNotFoundError:
            subprocess.run(
                ['xterm', '-e', 'bash', '-c', full_command],
                capture_output=True
            )

    return True


def _legacy_trigger_check(task, context):
    """旧版硬编码触发逻辑，向后兼容没有 trigger.eval 的任务"""
    now_str = context["now"].strftime("%H:%M")
    today_str = context["today"].isoformat()
    if task['trigger']['type'] == 'schedule':
        if task['trigger']['time'] != now_str:
            return False
        last_run = task.get('last_run', '')
        if last_run and last_run.startswith(today_str):
            return False
        return True
    return False


def _call_trigger_function(eval_path, context):
    """通过 importlib 加载并执行 trigger 函数"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("trigger_eval", eval_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.should_dispatch(context)


def evaluate_trigger(task, context):
    """评估任务是否应该发派：优先用编译生成的 trigger 函数，否则走旧逻辑"""
    eval_path = task.get('trigger', {}).get('eval')
    if eval_path:
        abs_path = os.path.expanduser(eval_path)
        if os.path.isfile(abs_path):
            return _call_trigger_function(abs_path, context)
    return _legacy_trigger_check(task, context)


def check_all_triggers():
    """检查所有 active 任务的触发条件"""
    tasks = load_manifest()
    now = datetime.datetime.now()

    context = {
        "now": now,
        "today": now.date(),
        "task_dir": BASE_DIR,
    }

    for task in tasks:
        if task['status'] != 'active':
            continue

        context["last_run"] = task.get('last_run')
        context["run_count"] = task.get('run_count', 0)

        if not evaluate_trigger(task, context):
            continue

        print(f"[{now.strftime('%H:%M')}] 发派任务: {task['name']} ({task['id']})")
        if dispatch(task):
            task['last_run'] = now.isoformat()
            task['run_count'] = task.get('run_count', 0) + 1
            save_manifest(tasks)


def list_tasks():
    """列出所有任务"""
    tasks = load_manifest()
    print(f"\n{'ID':<20} {'Name':<20} {'Trigger':<15} {'Eval':<8} {'Status':<10} {'Last Run':<20}")
    print('-' * 93)
    for t in tasks:
        trigger = t['trigger']['type']
        if trigger == 'schedule':
            trigger += f" @{t['trigger']['time']}"
        has_eval = 'yes' if t.get('trigger', {}).get('eval') else 'legacy'
        last_run = t.get('last_run', 'never') or 'never'
        print(f"{t['id']:<20} {t['name']:<20} {trigger:<15} {has_eval:<8} {t['status']:<10} {last_run:<20}")


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
    load_shell_env()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'list':
            list_tasks()
        elif cmd == 'run' and len(sys.argv) > 2:
            run_once(sys.argv[2])
        elif cmd == 'compile' and len(sys.argv) > 2:
            compile_task(sys.argv[2])
        else:
            print("Usage:")
            print("  dispatch.py                    # Start scheduler loop")
            print("  dispatch.py list               # List all tasks")
            print("  dispatch.py run <id>           # Trigger a task manually")
            print("  dispatch.py compile <id>       # Verify, test-run, and register a task")
    else:
        print("调度器运行中... (Ctrl+C 退出)")
        print("每分钟检查一次触发条件\n")
        try:
            while True:
                check_all_triggers()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n调度器已停止")
