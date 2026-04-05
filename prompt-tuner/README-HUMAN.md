# Prompt Tuner — Claude Code Skill

约束 Claude Code 在 prompt 调优时的行为纪律：先理解逻辑、拒绝硬编码、必须确认。

## 解决的问题

| 问题 | 此 skill 的约束 |
|------|----------------|
| 不看逻辑文档，直接改 prompt | ⛔ 必须先读文档，总结逻辑，用户确认后才能改 |
| 针对 case 硬编码特殊值 | ⛔ 所有修改必须是通用规则，禁止 case-specific 写法 |
| 只求通过 case，不确认逻辑 | ⛔ 每次修改必须向用户确认逻辑方向和副作用 |

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- 无其他依赖

## 安装到 Claude Code

```bash
cp -r prompt-tuner ~/.claude/skills/
```

## 使用方式

在 Claude Code 中说需要调优 prompt 时自动触发。

### 触发方式

- "这个 prompt 输出不对，帮我调一下"
- "这个 case 没通过，改 prompt"
- "prompt 调优"
- "调整提示词"

### 四阶段工作流

```
Phase 1: 理解（必须先做）
  ├── 读逻辑文档
  ├── 总结抽象逻辑
  └── 用户确认 ← ⛔ 不能跳过

Phase 2: 诊断
  ├── 分类根因（逻辑缺口/冲突/模糊/过拟合风险）
  └── 提出通用修复方向 → 用户确认

Phase 3: 编辑
  ├── 写通用规则，不是具体值
  ├── 扫描 diff 检查硬编码
  └── 说明影响范围和副作用

Phase 4: 验证
  ├── 测试原始 case
  ├── 测试相邻 case
  └── 用户确认无回归
```

### 反模式检测

此 skill 会让 Claude Code 拒绝以下行为：

- ❌ "当输入是 X 时输出 Y" → 硬编码
- ❌ 连续添加 if-exception → 过拟合
- ❌ "我觉得改这里就好，直接改" → 跳过确认
- ❌ "case 通过了！搞定" → 没测相邻 case

## 文件结构

```
prompt-tuner/
├── SKILL.md           # Claude Code 指令文件
└── README-HUMAN.md    # 本文件
```

## License

MIT
