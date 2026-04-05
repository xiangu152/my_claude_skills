---
name: prompt-tuner
description: "Structured prompt tuning workflow with logic-first discipline. Use when: (1) modifying system prompts, (2) fixing prompt behavior based on test cases, (3) iterating on prompt templates, (4) debugging prompt outputs. Triggers on 'tune prompt', 'fix prompt', 'prompt 调优', 'prompt 不对', '改 prompt', '调整提示词'. NOT for: writing prompts from scratch (use general coding), non-prompt code changes, or when no prompt file is involved."
---

# Prompt Tuner

Enforce a logic-first, generalization-required workflow for prompt tuning. Never hardcode. Never skip confirmation.

## ⛔ Absolute Rules

1. **NEVER hardcode case-specific values** in prompts to make a case pass
2. **NEVER skip logic confirmation** with the user before making changes
3. **NEVER edit a prompt without reading the logic documentation first**

Breaking any of these rules means the tuning session has failed. Stop and restart the workflow.

## Workflow

### Phase 1: Understand Before Touching

Before ANY prompt modification:

**Step 1.1 — Read all relevant logic documentation**

Look for and read:
- Any `*.md` files in the prompt's directory or parent directories
- Comments within the prompt file itself
- Test case files that describe expected behavior
- Any `LOGIC.md`, `DESIGN.md`, `RULES.md`, `README.md` near the prompt

```bash
# Find logic docs near the prompt
find . -name "*.md" -not -path "*/node_modules/*" | head -20
# Look for test cases
find . -name "*test*" -o -name "*case*" -o -name "*eval*" | grep -v node_modules
```

**Step 1.2 — Summarize the abstract logic**

After reading, write a summary in this format:

```
## Logic Summary

**Intent**: [One sentence describing what the prompt should achieve]

**Rules**:
1. [Abstract rule derived from docs, not from specific cases]
2. [Abstract rule...]
3. [Abstract rule...]

**Edge cases documented**:
- [If any are mentioned in docs]

**Ambiguities**:
- [Anything unclear that needs user input]
```

**Step 1.3 — Confirm with user**

Present the summary and ask:

> "根据文档，我理解逻辑是这样的：[summary]。这个理解对吗？有没有遗漏或错误？"

**Do NOT proceed until the user confirms.** If the user corrects you, update the summary and re-confirm.

### Phase 2: Diagnose the Problem

When a case fails or behavior is wrong:

**Step 2.1 — Classify the root cause**

| Category | Description | Correct Action |
|---|---|---|
| Logic gap | Prompt doesn't cover this scenario at all | Add general rule |
| Logic conflict | Prompt contradicts itself | Fix the conflict |
| Ambiguity | Prompt is vague, model interprets differently | Clarify the instruction |
| Overfitting risk | The "fix" would be case-specific | ❌ Stop. Generalize. |
| Case is wrong | The test case itself has wrong expectations | Discuss with user |

**Step 2.2 — Before proposing a fix, ask**

> "这个问题是 [category]。我的修复思路是 [general approach]，它会同时影响 [other scenarios]。你确认这个方向对吗？"

### Phase 3: Edit with Generalization

**Step 3.1 — Write the general rule, not the specific fix**

```
❌ BAD:  "当用户说'你好'时，回复'你好！有什么可以帮你的？'"
✅ GOOD: "对用户的问候语，用简洁友好的方式回应，并主动询问需求"

❌ BAD:  "如果输入包含数字3，输出'three'"
✅ GOOD: "将输入中的数字翻译为对应的英文单词"

❌ BAD:  "对于张三的问题，直接回答'A'"
✅ GOOD: "对于 [这类问题]，按照 [原则] 回答"
```

**Step 3.2 — Check for hardcoded values**

Before saving, scan the change:

```bash
# Check for suspicious patterns in the diff
git diff | grep -E "(具体值|当.*时.*输出|如果.*就.*回复)" 
```

If any hardcoding is found, rewrite it as a general rule.

**Step 3.3 — State the impact**

After editing, explicitly state:

```
## Change Summary

**What changed**: [Brief description]
**Generalization**: [The general rule this implements]
**Affected scenarios**: [What else this change impacts]
**Potential side effects**: [What could break]
```

### Phase 4: Validate

**Step 4.1 — Test the original case**

Run the failing case to confirm it passes now.

**Step 4.2 — Test neighboring cases**

Think of 2-3 similar but different cases and mentally trace through the prompt:
- Does the change break anything?
- Are there new edge cases introduced?

**Step 4.3 — Ask user to verify logic**

> "原始 case 通过了。但这个改动也会影响 [scenario A] 和 [scenario B]，按你的逻辑预期，它们应该 [expected behavior]。对吗？"

Only close the tuning session after user confirms no regressions.

## Anti-Patterns to Reject

When Claude Code (or you) detects these patterns, STOP:

### 1. Case-Specific Hardcoding
```
Prompt: "当输入是 X 时，输出 Y"
→ This is hardcoding. Reject.
→ Correct: "当输入满足 [general condition] 时，按照 [principle] 输出"
```

### 2. Brute-Force Patching
```
Adding exception after exception:
"If case A → do X"
"If case B → do Y"  
"If case C → do Z"
→ This is overfitting. Step back and find the unifying rule.
```

### 3. Confirmation Skipping
```
"I think the fix is to add '...' to the prompt. Let me just do it."
→ No. Present the logic summary first. Get confirmation.
```

### 4. Victory Declaring
```
"Case passes! Done!"
→ No. Test neighboring cases. Confirm logic with user. Then done.
```

## Prompt File Conventions

When working on prompts, look for these file patterns:

- `*.prompt.md`, `*.system.md`, `system_prompt.txt`
- `prompts/`, `templates/`, `config/prompts/`
- Any file containing "system:", "You are", "你的角色"
- YAML/JSON config files with `system_prompt` or `prompt` fields

## Quick Checklist

Before every prompt edit, run through this:

- [ ] Read logic documentation
- [ ] Summarized abstract logic
- [ ] User confirmed the logic
- [ ] Classified the root cause
- [ ] Proposed general (not specific) fix
- [ ] User confirmed the direction
- [ ] Edit contains no hardcoded values
- [ ] Tested original case
- [ ] Tested neighboring cases
- [ ] User confirmed no regressions
