---
name: self-improving-agent
description: 通用的自我改进 agent，从所有 skill 经验中学习。使用多内存架构（语义 + 情景 + 工作）持续演进代码库。通过 hooks 在 skill 完成/错误时自动触发基于自检的自我修正。
---

# Self-Improving Agent

> "一个从每次交互中学习的 AI agent，积累模式和洞察，持续改进自身能力。"

## 概述

这是一个**通用自我改进系统**，从所有 skill 经验中学习。它实现了一个完整的反馈循环：

- **多内存架构**：语义 + 情景 + 工作内存
- **自我修正**：检测并修复 skill 指导错误
- **自我验证**：定期验证 skill 准确性
- **Hooks 集成**：在 skill 事件时自动触发
- **演进标记**：可追溯的变更与来源归因

## 何时激活

### 自动触发（通过 hooks）

| 事件 | 触发 | 动作 |
|------|------|------|
| **before_start** | 任何 skill 启动 | 记录会话开始 |
| **after_complete** | 任何 skill 完成 | 提取模式，更新 skills |
| **on_error** | Bash 返回非零退出 | 捕获错误上下文，触发自我修正 |

### 手动触发

- 用户说"自我进化"、"self-improve"、"从经验中学习"
- 用户说"分析今天的经验"、"总结教训"
- 用户要求改进特定 skill

## 演进优先级矩阵

当新可重用知识出现时触发演进：

| 触发 | 目标 Skill | 优先级 | 动作 |
|------|-----------|--------|------|
| 发现新 PRD 模式 | prd-planner | 高 | 添加到质量检查清单 |
| 架构权衡明确 | architecting-solutions | 高 | 添加到决策模式 |
| API 设计规则学到 | api-designer | 高 | 更新模板 |
| 调试修复发现 | debugger | 高 | 添加到反模式 |
| 审查清单缺口 | code-reviewer | 高 | 添加清单项目 |
| 性能/安全洞察 | performance-engineer | 高 | 添加到模式 |
| UI/UX 规范问题 | prd-planner | 高 | 添加视觉规范要求 |

## 多内存架构

### 1. 语义内存（`memory/semantic-patterns.json`）

存储**可跨上下文重用的抽象模式和规则**：

```json
{
  "patterns": {
    "pattern_id": {
      "id": "pat-2025-01-11-001",
      "name": "Pattern Name",
      "source": "user_feedback|implementation_review|retrospective",
      "confidence": 0.95,
      "applications": 5,
      "created": "2025-01-11",
      "category": "prd_structure|react_patterns|async_patterns|...",
      "pattern": "One-line summary",
      "problem": "What problem does this solve?",
      "solution": { ... },
      "quality_rules": [ ... ],
      "target_skills": [ ... ]
    }
  }
}
```

### 2. 情景内存（`memory/episodic/`）

存储**具体经验及发生的事情**：

```
memory/episodic/
├── 2025/
│   ├── 2025-01-11-prd-creation.json
│   ├── 2025-01-11-debug-session.json
│   └── 2025-01-12-refactoring.json
```

```json
{
  "id": "ep-2025-01-11-001",
  "timestamp": "2025-01-11T10:30:00Z",
  "skill": "debugger",
  "situation": "User reported data not refreshing after form submission",
  "root_cause": "Empty callback in onRefresh prop",
  "solution": "Implement actual refresh logic in callback",
  "lesson": "Always verify callbacks are not empty functions",
  "related_pattern": "callback_verification",
  "user_feedback": {
    "rating": 8,
    "comments": "This was exactly the issue"
  }
}
```

### 3. 工作内存（`memory/working/`）

存储**当前会话上下文**：

```
memory/working/
├── current_session.json   # 活跃会话数据
├── last_error.json        # 错误上下文用于自我修正
└── session_end.json       # 会话结束标记
```

## 自我改进过程

### 阶段 1: 经验提取

任何 skill 完成后，提取：

```yaml
What happened:
  skill_used: {which skill}
  task: {what was being done}
  outcome: {success|partial|failure}

Key Insights:
  what_went_well: [what worked]
  what_went_wrong: [what didn't work]
  root_cause: {underlying issue if applicable}

User Feedback:
  rating: {1-10 if provided}
  comments: {specific feedback}
```

### 阶段 2: 模式抽象

将经验转换为可重用模式：

| 具体经验 | 抽象模式 | 目标 Skill |
|---------|---------|-----------|
| "User forgot to save PRD notes" | "Always persist thinking to files" | prd-planner |
| "Code review missed SQL injection" | "Add security checklist item" | code-reviewer |
| "Callback was empty, didn't work" | "Verify callback implementations" | debugger |
| "Net APY position ambiguous" | "UI specs need exact relative positions" | prd-planner |

**抽象规则：**

```yaml
If experience_repeats 3+ times:
  pattern_level: critical
  action: Add to skill's "Critical Mistakes" section

If solution_was_effective:
  pattern_level: best_practice
  action: Add to skill's "Best Practices" section

If user_rating >= 7:
  pattern_level: strength
  action: Reinforce this approach

If user_rating <= 4:
  pattern_level: weakness
  action: Add to "What to Avoid" section
```

### 阶段 3: Skill 更新

使用**演进标记**更新适当的 skill 文件：

```markdown
<!-- Evolution: 2025-01-12 | source: ep-2025-01-12-001 | skill: debugger -->

## Pattern Added (2025-01-12)

**Pattern**: Always verify callbacks are not empty functions

**Source**: Episode ep-2025-01-12-001

**Confidence**: 0.95

### Updated Checklist
- [ ] Verify all callbacks have implementations
- [ ] Test callback execution paths
```

**修正标记**（修复错误指导时）：

```markdown
<!-- Correction: 2025-01-12 | was: "Use callback chain" | reason: caused stale refresh -->

## Corrected Guidance

Use direct state monitoring instead of callback chains:
```typescript
// ✅ Do: Direct state monitoring
const prevPendingCount = usePrevious(pendingCount);
```
```

### 阶段 4: 内存整合

1. **更新语义内存**（`memory/semantic-patterns.json`）
2. **存储情景内存**（`memory/episodic/YYYY-MM-DD-{skill}.json`）
3. **基于应用/反馈更新模式置信度**
4. **剪枝过时模式**（低置信度、无近期应用）

## 自我修正（on_error hook）

触发条件：
- Bash 命令返回非零退出码
- 遵循 skill 指导后测试失败
- 用户报告指导产生错误结果

**过程：**

```markdown
## Self-Correction Workflow

1. Detect Error
   - 从 working/last_error.json 捕获错误上下文
   - 识别遵循了哪个 skill 指导

2. Verify Root Cause
   - Skill 指导不正确吗？
   - 指导被误解了吗？
   - 指导不完整吗？

3. Apply Correction
   - 用修正的指导更新 skill 文件
   - 添加带原因的修正标记
   - 在语义内存中更新相关模式

4. Validate Fix
   - 测试修正后的指导
   - 请用户验证
```

## 最佳实践

### 做

- ✅ 从每个 skill 交互中学习
- ✅ 在正确的抽象级别提取模式
- ✅ 更新多个相关 skills
- ✅ 跟踪置信度和应用计数
- ✅ 请求用户对改进的反馈
- ✅ 使用演进/修正标记以保持可追溯性
- ✅ 在广泛应用前验证指导

### 不做

- ❌ 从单一经验过度概括
- ❌ 没有置信度跟踪就更新 skills
- ❌ 忽略负面反馈
- ❌ 做破坏现有功能的更改
- ❌ 创建矛盾的模式
- ❌ 不理解上下文就更新 skills

## 快速开始

任何 skill 完成后，此 agent 自动：

1. **分析**发生了什么
2. **提取**模式和洞察
3. **更新**相关 skill 文件
4. **记录**到内存供将来参考
5. **报告**摘要给用户

## 参考

- [SimpleMem: Efficient Lifelong Memory for LLM Agents](https://arxiv.org/html/2601.02553v1)
- [Multi-Memory Survey](https://dl.acm.org/doi/10.1145/3748302)
- [Lifelong Learning of LLM based Agents](https://arxiv.org/html/2501.07278v1)
