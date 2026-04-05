---
name: skill-translator
description: "Translate OpenClaw skills into Claude Code skills. Use when: (1) user wants to adapt an OpenClaw skill for Claude Code, (2) migrating skills between platforms, (3) converting SKILL.md with OpenClaw metadata to Claude Code format. Triggers on 'translate skill', 'convert skill', 'adapt skill', 'openclaw skill to claude code'. NOT for: creating new skills from scratch (use skill-creator), installing skills (use install-skill)."
---

# Skill Translator

Translate OpenClaw skills into Claude Code compatible skills.

## Translation Process

### Step 1: Read the Source Skill

Read the OpenClaw skill's SKILL.md and list all files:

```bash
find /path/to/openclaw-skill -type f -not -path '*/.git/*' -not -path '*/.clawhub/*' -not -path '*_meta.json' | sort
```

Identify: SKILL.md, scripts/, references/, assets/, and any other resource files.

### Step 2: Create Target Directory

```bash
mkdir -p /path/to/target/skill-name/scripts
mkdir -p /path/to/target/skill-name/references  # if source has references/
mkdir -p /path/to/target/skill-name/assets       # if source has assets/
```

### Step 3: Translate SKILL.md

Apply these transformations:

#### Frontmatter

**Keep only `name` and `description`.** Remove all other OpenClaw fields:

| OpenClaw field | Action |
|---|---|
| `name` | ✅ Keep |
| `description` | ✅ Keep, but review and update |
| `slug` | ❌ Remove |
| `version` | ❌ Remove |
| `homepage` | ❌ Remove |
| `changelog` | ❌ Remove |
| `metadata` (clawdbot/openclaw) | ❌ Remove entirely |

If the description mentions "Codex", "OpenClaw", or platform-specific triggers, update to Claude Code context.

Example transformation:

```yaml
# ❌ OpenClaw format
---
name: my-skill
slug: my-skill
version: 1.0.0
homepage: https://clawic.com/skills/my-skill
description: "Does X. Use when Y."
metadata: {"clawdbot":{"emoji":"🔧","requires":{"bins":["tool"]},"os":["darwin","linux","win32"]}}
---

# ✅ Claude Code format
---
name: my-skill
description: "Does X. Use when Y. NOT for: Z."
---
```

#### Body Content

1. **Replace `{baseDir}`** with `$SCRIPT_DIR` or relative paths like `scripts/search.mjs`
2. **Replace "Codex"** references with "Claude Code"
3. **Remove OpenClaw config blocks** — JSON config examples for OpenClaw's `skills.entries` are irrelevant
4. **Remove environment variable OpenClaw config** — Keep `export VAR=value` shell instructions, remove OpenClaw JSON config
5. **Remove "Related Skills"** sections mentioning `clawhub install` — Claude Code uses `cp -r`
6. **Remove "Feedback"** sections mentioning `clawhub star` / `clawhub sync`
7. **Keep all functional content** — Commands, workflows, examples, tips, traps

#### Path Transformations

| OpenClaw | Claude Code |
|---|---|
| `{baseDir}/scripts/foo.mjs` | `$SCRIPT_DIR/scripts/foo.mjs` or `scripts/foo.mjs` |
| OpenClaw skill install | `cp -r skill-name ~/.claude/skills/` |

### Step 4: Copy Resource Files

Copy scripts, references, and assets as-is:

```bash
# Scripts
cp -r /path/to/source/scripts/* /path/to/target/skill-name/scripts/

# References (if exist)
cp -r /path/to/source/references/* /path/to/target/skill-name/references/ 2>/dev/null

# Assets (if exist)
cp -r /path/to/source/assets/* /path/to/target/skill-name/assets/ 2>/dev/null
```

Check script paths inside SKILL.md match the copied location.

### Step 5: Create README-HUMAN.md

Claude Code skills need a Chinese-language `README-HUMAN.md`. Create it with this structure:

```markdown
# <Skill Name> — Claude Code Skill

<简短中文描述，说明这个 skill 做什么>

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- <列出其他依赖>

## 依赖安装

<如有，列出 pip/npm 安装命令>

## 安装到 Claude Code

```bash
cp -r skill-name ~/.claude/skills/
```

## 验证

<列出验证命令>

## 使用方式

<说明如何触发此 skill>

## 文件结构

```
skill-name/
├── SKILL.md
├── README-HUMAN.md
└── scripts/ (如有)
```

## License

<许可证信息>
```

### Step 6: Verify

1. Check file structure:
```bash
find /path/to/target/skill-name -type f
```

2. Verify SKILL.md frontmatter has only `name` and `description`

3. Verify no OpenClaw-specific syntax remains:
```bash
grep -n "baseDir\|clawdbot\|clawhub\|clawic\|openclaw\|Codex" /path/to/target/skill-name/SKILL.md
# Should return nothing (or only intentional references)
```

4. Install and test:
```bash
rm -rf ~/.claude/skills/skill-name
cp -r /path/to/target/skill-name ~/.claude/skills/skill-name
```

## Differences Reference

### OpenClaw vs Claude Code Skill Format

| Aspect | OpenClaw | Claude Code |
|---|---|---|
| Frontmatter fields | name, description, slug, version, homepage, changelog, metadata | name, description only |
| Metadata | `metadata: {"clawdbot":{...}}` with emoji, requires, os | None |
| Path variable | `{baseDir}` | `$SCRIPT_DIR` or relative |
| Config | JSON in `skills.entries` | Environment variables |
| Install method | `clawhub install` or manual | `cp -r` to `~/.claude/skills/` |
| Human docs | Optional | README-HUMAN.md (required, Chinese) |
| Directory | `~/.openclaw/workspace/skills/` | `~/.claude/skills/` |
