---
name: install-skill
description: Install a skill into Claude Code. Use when the user wants to add a new skill, install a skill from a local folder, or set up a custom skill. Triggers on "install skill", "add skill", "set up skill", "load skill".
---

# Install Skill

You are helping the user install a skill into Claude Code. Follow these steps precisely.

## Step 1: Identify the Skill Source

Ask the user where the skill is. It can be:
- A local folder path on their machine
- A git repository URL
- An inline description (you'll create it from scratch)

## Step 2: Read the Skill

If it's a local folder, read the contents:
- Check for `SKILL.md` — this is the entry point
- Check for `scripts/`, `templates/`, or other supporting files
- Read `SKILL.md` fully to understand what the skill does and what it needs

If it's a git repo, clone it to a temp directory first:
```bash
git clone <url> /tmp/skill-to-install
```

## Step 3: Check Dependencies

From `SKILL.md`, identify:
- **Required environment variables** (look for mentions of API keys, tokens, env vars)
- **Required CLI tools** (look for mentions of `node`, `python`, `curl`, etc.)
- **Required npm/pip packages** (look for import statements or dependency mentions)

Verify each:
```bash
# Check env vars
echo $ENV_VAR_NAME

# Check CLI tools
which node
which python3

# Check packages
node -e "require('package-name')" 2>/dev/null && echo "OK" || echo "MISSING"
```

If anything is missing, tell the user what's needed and how to install it. Do NOT proceed until dependencies are satisfied.

## Step 4: Install the Skill

Copy the skill folder to the personal skills directory.

**⚠️ 关键规则 — 避免嵌套目录：**
- `cp -r 源目录/ 目标目录` 如果目标目录**已存在**，cp 会把源目录复制到目标目录**里面**，产生 `skill-name/skill-name/` 嵌套！
- 正确做法：**先删除旧版本（如果有），再复制。目标目录不能预先存在。**
- 复制后必须用 `find` 验证文件结构，不能只靠回忆复述文件名。

**macOS / Linux:**
```bash
# 先清理旧版本（避免嵌套）
rm -rf ~/.claude/skills/<skill-name>
# 再复制
cp -r /path/to/skill-folder ~/.claude/skills/<skill-name>
```

**Windows (WSL):**
```bash
rm -rf ~/.claude/skills/<skill-name>
cp -r /path/to/skill-folder ~/.claude/skills/<skill-name>
```

**Windows (PowerShell):**
```powershell
if (Test-Path "$env:USERPROFILE\.claude\skills\<skill-name>") { Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\skills\<skill-name>" }
Copy-Item -Recurse "C:\path\to\skill-folder" "$env:USERPROFILE\.claude\skills\<skill-name>"
```

如果源目录名与 `<skill-name>` 不一致，需要重命名：
```bash
rm -rf ~/.claude/skills/<skill-name>
cp -r /path/to/源目录名 ~/.claude/skills/<skill-name>
```

## Step 5: Set Up Environment Variables

If the skill requires environment variables that aren't set:

**macOS / Linux (zsh):**
```bash
echo 'export VAR_NAME="value"' >> ~/.zshrc
source ~/.zshrc
```

**macOS / Linux (bash):**
```bash
echo 'export VAR_NAME="value"' >> ~/.bashrc
source ~/.bashrc
```

**Windows (PowerShell):**
```powershell
[Environment]::SetEnvironmentVariable("VAR_NAME", "value", "User")
```

Tell the user they may need to restart their terminal or Claude Code for env vars to take effect.

## Step 6: Verify

1. **用 `find` 列出实际文件结构**（不要只用 `ls`，不要自己回忆文件名）：
```bash
find ~/.claude/skills/<skill-name> -type f
```

2. **检查是否产生嵌套** — 如果看到 `<skill-name>/<skill-name>/` 结构，说明安装出错了，需要重新执行 Step 4：
```bash
# 如果检测到嵌套，修复：
rm -rf ~/.claude/skills/<skill-name>
cp -r /path/to/skill-folder/. ~/.claude/skills/<skill-name>
```

3. **检查脚本权限**（如果 skill 有 scripts/ 目录）：
```bash
ls -la ~/.claude/skills/<skill-name>/scripts/
# 如果 .sh 文件不可执行：
chmod +x ~/.claude/skills/<skill-name>/scripts/*.sh
```

4. **如果 skill 有可执行脚本，做一次 dry run 测试**：
```bash
# 根据实际脚本文件名调整，查看 SKILL.md 中的 Usage 部分
node ~/.claude/skills/<skill-name>/scripts/search.mjs --help
# 或
python ~/.claude/skills/<skill-name>/scripts/main.py --help
```

5. Restart Claude Code (exit and re-run `claude`) for the new skill to be recognized.

6. Tell the user to try invoking it with `/<skill-name>` or by asking a question that matches the skill's description.

## Summary Template

After installation, report to the user:

```
✅ Skill "<skill-name>" installed successfully!

📁 Location: ~/.claude/skills/<skill-name>/
🔧 Dependencies: <list what was checked/set up>
🔑 Env vars: <list what was configured>
💬 Invoke with: /<skill-name> or ask about <description>
⚠️ Restart Claude Code to pick up the new skill.
```
