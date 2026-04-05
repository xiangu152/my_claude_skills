# Startup Manifest Template

## Metadata
- **Version**: 1.0
- **Last Updated**: [ISO timestamp]
- **Owner**: [who maintains this]

## Environment Dependencies

### Required Environment Variables
| Variable | Description | Example | Status |
|----------|-------------|---------|--------|
| `FEISHU_APP_ID` | Feishu app ID | `cli_xxx` | ⬜ Not set |
| `FEISHU_APP_SECRET` | Feishu app secret | `xxx` | ⬜ Not set |
| `TAVILY_API_KEY` | Tavily API key | `tvly_xxx` | ⬜ Not set |

### Required Tools
| Tool | Command to Check | Status |
|------|------------------|--------|
| Node.js | `node --version` | ⬜ Not checked |
| Python | `python3 --version` | ⬜ Not checked |
| Git | `git --version` | ⬜ Not checked |

### Required Files
| Path | Description | Status |
|------|-------------|--------|
| `~/.claude/workspace/SOUL.md` | Identity file | ⬜ Not checked |
| `~/.claude/workspace/USER.md` | User profile | ⬜ Not checked |
| `./config.json` | Project config | ⬜ Not checked |

## Startup Sequence

### Step 1: Validate Environment
```bash
# Check env vars
[ -z "$FEISHU_APP_ID" ] && echo "Missing FEISHU_APP_ID"
[ -z "$TAVILY_API_KEY" ] && echo "Missing TAVILY_API_KEY"

# Check tools
node --version > /dev/null 2>&1 || echo "Node.js not found"
```

### Step 2: Load Context Files
1. Read `~/.claude/workspace/SOUL.md`
2. Read `~/.claude/workspace/USER.md`
3. Read `./README.md` (if exists)
4. Read `./AGENTS.md` (if exists)

### Step 3: Execute Startup Commands
```bash
# Example: Activate virtual environment
# source venv/bin/activate

# Example: Load environment variables
# export $(cat .env | xargs)

# Example: Check project status
# git status --short
```

### Step 4: Report Status
```
Startup complete:
✓ Environment validated
✓ Context loaded
✓ Ready for work
```

## Custom Tasks

### Task: Prompt Tuning
- **Trigger**: When working on prompt optimization
- **Files to load**: `prompts/`, `test-cases/`
- **Validation**: Check `prompt-tuner` skill is installed

### Task: Patent Writing
- **Trigger**: When working on patent applications
- **Files to load**: `patent-templates/`, `code-analysis.md`
- **Validation**: Check `patent-writer`, `tavily-search`, `word-docx` skills

## Notes
[Any additional notes or reminders]
