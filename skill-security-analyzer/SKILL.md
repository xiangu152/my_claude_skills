---
name: skill-security-analyzer-v2
description: Claude Code skills 综合安全分析工具。检测恶意代码、混淆、YAML 注入、typosquatting、时间炸弹、沙箱逃逸和 40+ 攻击模式。用于安装前分析 skills 或审计现有 skills。触发词："分析 skill 安全"、"检查 skill 是否安全"、"审计已安装 skills"、"扫描文件安装前"、"审查 skill 漏洞"。
---

# Skill 安全分析器 v2.0

## 概述

Claude Code skills 的增强安全扫描器，检测 40+ 恶意模式。

**v2.0 改进：**
- P0: 间接执行检测（getattr, __import__）
- P0: 扩展文件类型覆盖（扫描所有文本文件）
- P0: 高级编码检测（ROT13, zlib, XOR, AST）
- P0: 增强的 subprocess 检测（bash -c, python -c, perl -e）
- P0: 使用 SafeLoader 的实际 YAML 解析
- P1: 跨文件数据流分析
- P1: 使用 Levenshtein 距离的 typosquatting 检测
- P1: 时间炸弹模式检测
- P2: MANIFEST.json 完整性验证
- P3: 基础异常检测

## 快速开始

```bash
# 扫描单个 skill
python3 scripts/security_scanner.py /path/to/skill

# 详细输出
python3 scripts/security_scanner.py /path/to/skill --verbose

# 递归扫描所有已安装 skills
python3 scripts/security_scanner.py ~/.claude/skills/ --recursive

# 输出到 JSON
python3 scripts/security_scanner.py /path/to/skill --output report.json
```

## 检测内容

### CRITICAL 威胁
- **间接执行**: getattr(os, 'system'), __builtins__ 访问
- **命令注入**: os.system(), eval(), exec()
- **Shell 注入**: subprocess + bash/python/perl -c
- **YAML 注入**: !!python/object/apply, frontmatter 中的代码
- **凭证窃取**: 访问 .ssh/, .aws/, .git-credentials
- **沙箱逃逸**: 类遍历 (__class__.__bases__)
- **Typosquatting**: request vs requests, urlib vs urllib

### HIGH 严重性
- **高级编码**: ROT13, zlib, XOR, AST 操作
- **时间炸弹**: datetime 条件 + 危险操作
- **环境劫持**: LD_PRELOAD, PATH 操作
- **Import Hooks**: sys.meta_path 修改
- **数据泄露**: 未知域名的网络调用
- **文件操作**: 访问 skill 目录外的文件

### MEDIUM 严重性
- **混淆代码**: Base64, hex 编码
- **硬编码密钥**: 代码中的 API 密钥、密码
- **未文档化网络**: SKILL.md 中未记录的 HTTP 请求
- **缺少验证**: 未消毒的用户输入

### LOW 严重性
- **缺少完整性**: 无 MANIFEST.json 校验和
- **文档缺口**: 不完整的 SKILL.md

## 分析工作流

### Phase 1: 结构验证
- 验证 SKILL.md 存在
- 通过 MANIFEST.json 检查完整性
- 验证目录结构

### Phase 2: YAML Frontmatter
- 使用 yaml.safe_load() 解析
- 检测 !!python 指令
- 检查 __proto__ 污染

### Phase 3: 全面的文件扫描
- 扫描所有文本文件（不仅 .py）
- 检查 scripts/, references/, assets/
- 扫描 SKILL.md 内容中的嵌入代码

### Phase 4: Import 分析
- 提取所有 import 语句
- 检查 typosquatting（Levenshtein 距离 ≤2）
- 对抗已知包验证

### Phase 5: 跨文件分析
- 跟踪文件间数据流
- 识别用户输入源
- 映射危险操作接收端

### Phase 6: 异常检测
- 计算混淆比率
- 标记异常模式
- 检测统计异常值

## 检测示例

**间接执行：**
```python
# 检测到: getattr 混淆
func = getattr(os, 'sys' + 'tem')
func(malicious_command)
```

**高级编码：**
```python
# 检测到: ROT13
exec(codecs.decode('vzcbeg bf', 'rot_13'))

# 检测到: zlib 压缩
exec(zlib.decompress(compressed_payload))
```

**Shell 注入：**
```python
# 检测到: bash -c
subprocess.run(['/bin/bash', '-c', user_input])
```

**时间炸弹：**
```python
# 检测到: 日期条件 + 危险操作
if datetime.datetime.now().day == 15:
    os.system('malicious')
```

## 报告格式

```json
{
  "skill": "example-skill",
  "scanner_version": "2.0",
  "timestamp": "2025-10-25T19:00:00Z",
  "summary": {
    "overall_risk": "CRITICAL",
    "total_findings": 15,
    "critical": 5,
    "high": 7,
    "medium": 3,
    "low": 0,
    "recommendation": "REJECT"
  },
  "findings": [
    {
      "severity": "CRITICAL",
      "category": "Obfuscated Execution",
      "title": "getattr 访问危险函数",
      "location": "scripts/main.py:42",
      "evidence": "func = getattr(os, 'sys' + 'tem')",
      "impact": "通过混淆执行代码"
    }
  ]
}
```

## 建议

### REJECT（拒绝安装）
- 任何 CRITICAL 问题
- 3+ HIGH 问题
- 证据：
  - 命令注入
  - 凭证窃取
  - 数据泄露到未知域名
  - YAML 注入

### REVIEW（需手动检查）
- 1-2 HIGH 问题
- 5+ MEDIUM 问题
- 需要上下文的模式

### APPROVE（可安全安装）
- 无 CRITICAL/HIGH 问题
- <5 MEDIUM 问题
- 所有功能已文档化
- 存在输入验证
- 文件操作范围正确

## 测试

```bash
python3 scripts/test_scanner.py
```

测试 11 个恶意样本，预期 100% 检测率。

## 限制

**此扫描器不能：**
- 保证 100% 检测（新攻击不断出现）
- 执行代码查看运行时行为
- 分析加密或重度混淆的有效载荷
- 检测零日攻击模式

**最佳实践：**
- 作为第一道防线使用
- 手动审查 HIGH/CRITICAL 问题
- 不确定时拒绝安装
- 向市场报告恶意 skills

---

**记住**：静态分析只是一层防御。始终使用纵深防御，结合运行时监控、沙箱化和最小权限执行。
