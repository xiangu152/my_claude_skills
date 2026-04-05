#!/usr/bin/env node
/**
 * 文件变化调度器 — 监控文件变化，发派任务
 * 只监控文件，不做调度决策，调度逻辑由编译时确定。
 */

const fs = require('fs');
const { exec } = require('child_process');
const path = require('path');

const MANIFEST = 'task-manifest.json';

function loadTasks() {
  return JSON.parse(fs.readFileSync(MANIFEST, 'utf8')).tasks;
}

function saveManifest(tasks) {
  const data = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
  data.tasks = tasks;
  fs.writeFileSync(MANIFEST, JSON.stringify(data, null, 2));
}

function getTaskConfig(task) {
  return JSON.stringify(task, null, 2);
}

function compileDispatchCommand(task) {
  const config = getTaskConfig(task);
  const instruction = task.task.instruction;
  const skills = (task.task.skills || []).join(', ');
  const deliveryPath = task.delivery.path;
  const logPath = task.delivery.log_path;

  const lines = [
    '你正在执行一个自动化任务。',
    '',
    '任务配置：',
    '```json',
    config,
    '```',
    '',
    '请执行：' + instruction,
    '结果写入：' + deliveryPath,
    '日志追加到：' + logPath,
    'Skills：' + skills,
    '完成后退出。'
  ];
  const prompt = lines.join('\\n');
  const escaped = prompt.replace(/"/g, '\\"');
  return 'claude --permission-mode bypassPermissions --print "' + escaped + '"';
}

function dispatch(task) {
  const command = compileDispatchCommand(task);

  if (process.platform === 'darwin') {
    var escaped = command.replace(/"/g, '\\"');
    var script = 'tell application "Terminal" to activate\n' +
      'set newTab to do script "' + escaped + '"\n' +
      'delay 0.5\n' +
      'repeat while busy of newTab\n' +
      '  delay 1\n' +
      'end repeat\n' +
      'close newTab';
    exec('osascript -e ' + JSON.stringify(script));
  } else if (process.platform === 'win32') {
    exec('cmd /c start cmd /c "' + command + '"');
  } else {
    exec("gnome-terminal -- bash -c '" + command + "; exit'");
  }

  // Update last_run
  const data = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
  const target = data.tasks.find(function(t) { return t.id === task.id; });
  if (target) {
    target.last_run = new Date().toISOString();
    target.run_count = (target.run_count || 0) + 1;
    fs.writeFileSync(MANIFEST, JSON.stringify(data, null, 2));
  }

  return true;
}

function listTasks() {
  const tasks = loadTasks();
  console.log('\nID                  Name                Trigger          Status     Last Run');
  console.log('-'.repeat(90));
  tasks.forEach(function(t) {
    var trigger = t.trigger.type;
    if (trigger === 'schedule') trigger += ' @' + t.trigger.time;
    if (trigger === 'file_watch') trigger += ' ' + t.trigger.file;
    var lastRun = t.last_run || 'never';
    console.log(t.id.padEnd(20) + t.name.padEnd(20) + trigger.padEnd(17) + t.status.padEnd(11) + lastRun);
  });
}

function runOnce(taskId) {
  const tasks = loadTasks();
  const task = tasks.find(function(t) { return t.id === taskId; });
  if (!task) {
    console.error('Task not found: ' + taskId);
    return;
  }
  console.log('手动触发: ' + task.name + ' (' + task.id + ')');
  dispatch(task);
}

// Main
const args = process.argv.slice(2);
const cmd = args[0];

if (cmd === 'list') {
  listTasks();
} else if (cmd === 'run' && args[1]) {
  runOnce(args[1]);
} else {
  // Start file watch mode
  const tasks = loadTasks();
  const watchTasks = tasks.filter(function(t) {
    return t.status === 'active' && t.trigger && t.trigger.type === 'file_watch';
  });

  if (watchTasks.length === 0) {
    console.log('No file_watch tasks configured.');
    console.log('Usage:');
    console.log('  node file_watch.js          # Start file watcher');
    console.log('  node file_watch.js list     # List all tasks');
    console.log('  node file_watch.js run <id> # Trigger a task manually');
    process.exit(0);
  }

  const watchers = {};

  watchTasks.forEach(function(task) {
    const watchFile = task.trigger.file;
    const absPath = path.resolve(watchFile);

    if (!fs.existsSync(absPath)) {
      console.log('File not found, skipping: ' + watchFile);
      return;
    }

    console.log('监控: ' + watchFile + ' -> ' + task.name + ' (' + task.id + ')');

    fs.watchFile(absPath, { interval: 5000 }, function(curr, prev) {
      if (curr.mtime > prev.mtime) {
        console.log('[' + new Date().toISOString() + '] 文件变化: ' + watchFile);
        dispatch(task);
      }
    });
    watchers[task.id] = true;
  });

  console.log('\n文件变化调度器运行中... (监控 ' + Object.keys(watchers).length + ' 个文件, Ctrl+C 退出)');

  process.on('SIGINT', function() {
    console.log('\n停止监控...');
    watchTasks.forEach(function(task) {
      fs.unwatchFile(path.resolve(task.trigger.file));
    });
    process.exit(0);
  });
}
