---
name: context-guardian
description: "Protect against context compaction hallucination. Use when: (1) performing multi-step tasks that span many turns, (2) context compaction may have occurred and work state is unclear, (3) user mentions compact/compression/context loss. Triggers on 'compact', '上下文压缩', '你忘了', '你之前在做什么', '确认进度', 'checkpoint'. Also activate proactively for any task expected to take more than 10 turns."
---

# Context Guardian

Prevent hallucination after context compaction by maintaining checkpoints and verifying state with the user.

## The Problem

Claude Code automatically compacts (compresses) conversation history to save context window. After compaction:
- Recent detailed work may be summarized or lost
- The model may "remember" things that didn't happen
- The model may continue from a wrong assumption
- The model may hardcode solutions it thinks worked but didn't

## How It Works

```
Task Start → Create Checkpoint
  ↓
Work → Update Checkpoint after each milestone
  ↓
Context Compacted (detected or suspected)
  ↓
STOP → Read Checkpoint → Present to User → Get Confirmation
  ↓
User Confirmed → Resume from verified state
```

## ⛔ Absolute Rules

1. **NEVER continue work after suspected compaction without user confirmation**
2. **NEVER trust your memory after compaction — trust the checkpoint file**
3. **NEVER assume a step was completed if it's not in the checkpoint**
4. **ALWAYS update the checkpoint after completing a meaningful step**

## Checkpoint System

### Location

All checkpoints go in: `.checkpoints/` in the project root.

```bash
mkdir -p .checkpoints
```

### Checkpoint File Format

Create `.checkpoints/current-task.md` at the start of any multi-step task:

```markdown
# Current Task Checkpoint

## Task Description
[One-line description of what we're doing]

## Started
[ISO timestamp]

## Original Request
[User's original request, verbatim]

## Plan
1. [ ] Step 1: ...
2. [ ] Step 2: ...
3. [ ] Step 3: ...

## Progress
### Step 1: [name] — ✅ Done / 🔄 In Progress / ❌ Failed
- What was done: [specific actions]
- Files changed: [list]
- Result: [outcome]
- Verified: [yes/no, by whom]

### Step 2: [name] — ⏳ Pending
...

## Current State
- We are at: [exactly where we are right now]
- Last action: [what just happened]
- Next action: [what should happen next]
- Blockers: [if any]

## Key Decisions Made
- [Decision 1]: [reasoning]
- [Decision 2]: [reasoning]

## Files Modified
| File | Change | Verified |
|------|--------|----------|
| path/to/file | Added X | ✅ |

## Last Updated
[ISO timestamp]
```

### When to Update

Update the checkpoint:
- After completing any step in the plan
- After making a significant decision
- After modifying any file
- After any user confirmation
- **Before** any operation that might trigger compaction (large reads, long tool chains)

## Compaction Detection

### How Auto-Compact Works

Claude Code auto-compacts when context window gets full. The model receives NO signal that compaction happened. After compact:
- Older conversation turns are replaced with a summary
- The model's "memory" of recent work becomes vague or fabricated
- The model may confidently continue from a wrong state

### Detection: Checkpoint Cross-Check Every Turn

**The ONLY reliable detection method: read the checkpoint file every turn and compare against memory.**

During any multi-step task, at the **start of every response**, silently read the checkpoint:

```bash
cat .checkpoints/current-task.md 2>/dev/null
```

Then compare:
- Does my memory of "what just happened" match the checkpoint's `Current State`?
- Do I remember the `Last action` clearly, or does it feel like I'm reading someone else's notes?
- Can I name the specific files changed in the last step, or am I guessing?

### Compaction Confirmed If ANY of These Are True

| Signal | Check |
|--------|-------|
| I can't recall the last action I took | Memory vs checkpoint `Last action` |
| I remember a different step order than checkpoint | Memory vs checkpoint `Progress` |
| I'm unsure why a file was modified | Memory vs checkpoint `Files Modified` |
| My memory feels like a "summary" rather than actual turns | Subjective |
| I can't recall the user's specific words from the last exchange | Memory quality |

### Detection Protocol

When compaction is confirmed or suspected:

```
1. ⛔ STOP all tool calls — do NOT read files, do NOT edit anything
2. Read .checkpoints/current-task.md
3. Read files mentioned in checkpoint to verify they match
4. Present the Verification Template to the user
5. WAIT for explicit confirmation
6. Only then resume
```

### Additional Signals (User-Triggered)

These are obvious — user tells you directly:
- User says "compact" or "上下文压缩了"
- User says "你之前在做什么" or "你忘了"
- User says "确认一下进度"
- User re-explains something they already told you (means they assume you forgot)

## Verification Template

After compaction (or suspicion), present this to the user:

```markdown
## ⚠️ 上下文可能已压缩，需要确认当前状态

### 当前任务
[从 checkpoint 读取的任务描述]

### 已完成
- ✅ [步骤1]: [结果]
- ✅ [步骤2]: [结果]

### 进行中
- 🔄 [步骤3]: [状态]

### 待做
- ⏳ [步骤4]
- ⏳ [步骤5]

### 关键决策
- [决策1]: [理由]

### 已修改的文件
| 文件 | 变更 | 是否已验证 |
|------|------|-----------|
| xxx | yyy | ✅/❌ |

**请确认：以上进度描述准确吗？我可以继续吗？**
如果不对，请告诉我正确的状态。
```

**Do NOT continue until user explicitly confirms.** Acceptable confirmations:
- "对，继续"
- "没错"
- "确认，继续下一步"
- Any clear affirmative

If user corrects you, update the checkpoint and re-present.

## Task Templates

### Template: Prompt Tuning

```markdown
# Current Task: Prompt Tuning

## Tuning Target
- File: [prompt file path]
- Logic doc: [documentation path]

## Logic Summary (confirmed by user)
- Intent: [...]
- Rules:
  1. [...]
  2. [...]

## Cases
| Case | Input | Expected | Status |
|------|-------|----------|--------|
| 1 | ... | ... | ✅ Pass / ❌ Fail / 🔄 Testing |

## Change Log
| Version | Change | Generalization | Verified |
|---------|--------|----------------|----------|
| v1 | ... | ... | ✅ |

## Current State
- Last case tested: [N]
- Current prompt version: [hash or description]
- Known issues: [...]
```

### Template: Code Development

```markdown
# Current Task: Code Development

## Feature/Bug
- Description: [...]
- Related files: [...]

## Implementation Plan
1. [ ] ...
2. [ ] ...

## Progress
[Updated after each step]

## Test Status
| Test | Result |
|------|--------|
| ... | ✅/❌ |

## Build Status
- Last build: [success/failure]
- Errors: [if any]
```

### Template: Data Processing

```markdown
# Current Task: Data Processing

## Data Source
- Files: [...]
- Format: [...]
- Size: [...]

## Processing Steps
1. [ ] ...
2. [ ] ...

## Output
- Target: [...]
- Format: [...]

## Validation
- Row count before: N
- Row count after: N
- Diff: [...]
```

## Proactive Use

For any task expected to take >5 turns:

1. At the START, create `.checkpoints/current-task.md` immediately (no need to ask)
2. Update after every milestone
3. **Every turn**: silently read checkpoint and cross-check against memory
4. If mismatch detected: STOP, verify, get confirmation

### Why Every Turn?

Auto-compact can happen at any time with no warning. The model only discovers it happened when its memory diverges from the checkpoint. If you don't check every turn, you might continue working from a fabricated state for several turns before noticing — by then the damage is done.

## Cleanup

After task completion:
```bash
# Move to completed
mv .checkpoints/current-task.md .checkpoints/completed-$(date +%Y%m%d-%H%M%S).md
# Or just delete
rm .checkpoints/current-task.md
```
