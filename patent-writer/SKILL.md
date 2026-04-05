---
name: patent-writer
description: "Patent application drafting based on codebase analysis. Use when: (1) writing patent applications from code, (2) drafting invention disclosures, (3) preparing patent claims. Triggers on 'patent', '专利', 'write patent', 'patent application', 'invention disclosure', '撰写专利'. Requires: user must provide a DOCX template file. NOT for: legal advice, patent search (freedom-to-operate), or when no codebase is involved."
---

# Patent Writer

Draft patent applications from codebases. Write section by section, research every claim, cite every source.

## ⛔ Absolute Rules

1. **NEVER generate technical content from memory** — every technical claim must come from codebase analysis or web research
2. **NEVER fabricate references** — every cited source must have a verifiable URL
3. **NEVER skip research** — before writing any section, search for related prior art and real patent examples
4. **NEVER write the full document at once** — write one section, get user approval, then continue
5. **NEVER guess the architecture** — always confirm with user before writing

## Prerequisites

- Codebase to analyze
- DOCX template provided by user (patent format)
- Skills installed: `tavily-search`, `word-docx`, `agent-browser` (optional)

## Workflow

### Phase 1: Codebase Analysis & Template Reading

**Step 1.1 — Read the DOCX template first**

Before touching the code, read the user's template to understand the required structure:

```bash
python3 -c "
from docx import Document
doc = Document('[user_template_path]')
for i, p in enumerate(doc.paragraphs[:50]):
    if p.text.strip():
        print(f'{i}: [{p.style.name}] {p.text[:100]}')
"
```

Identify:
- Which sections the template requires
- Any pre-filled content or examples in the template
- Style conventions (heading levels, font, spacing)
- Placeholder text that indicates expected content

**Step 1.2 — Present template structure to user**

```
## 模板结构分析

| 章节 | 模板要求 | 备注 |
|------|----------|------|
| 技术领域 | [有/无] | [说明] |
| 背景技术 | [有/无] | [说明] |
| ... | ... | ... |

模板中已有内容：[列出]
模板风格要求：[说明]
```

**Step 1.3 — Scan the codebase**

```bash
# Understand project structure
find . -type f -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.rs" | head -50
# Find main entry points
find . -name "main.*" -o -name "app.*" -o -name "index.*" | head -20
# Find config/architecture docs
find . -name "*.md" -name "*README*" -o -name "*ARCHITECTURE*" -o -name "*DESIGN*" | head -10
```

Read the key files to understand:
- What problem does this solve?
- What is the technical approach?
- What is novel vs. existing solutions?

**Step 1.2 — Present findings to user**

```
## 代码仓分析结果

### 解决的问题
[从代码中推断的问题描述]

### 技术方案
[从代码中提取的核心技术路径]

### 核心模块
| 模块 | 文件 | 作用 |
|------|------|------|
| ... | ... | ... |

### 我认为的创新点（请确认或修正）
1. [创新点1]
2. [创新点2]
3. [创新点3]

请确认以上理解是否正确，补充或修正创新点。
```

**Do NOT proceed until user confirms.**

### Phase 2: Innovation Discussion

After user confirms codebase analysis AND template is understood:

**Step 2.1 — Structured discussion based on template**

Use the template structure to guide the discussion. For each template section, discuss what content fits:

> "模板要求 [章节名]。根据代码分析，这一节我计划写 [内容概要]。你的想法是什么？"

This ensures the discussion maps directly to the final output format.

**Step 2.2 — Deep-dive on each innovation point**

For each confirmed innovation point, ask:

> "关于创新点 [N]：[描述]。这个创新点的技术细节是什么？与现有方案的关键区别在哪里？请尽量详细说明。"

Record all user input verbatim — this is the primary source of technical content.

**Step 2.2 — Confirm the claim structure**

```
## 权利要求结构（草案）

### 独立权利要求
[核心方法/系统/装置的权利要求]

### 从属权利要求
1. [从属权利要求1]
2. [从属权利要求2]
...

请确认这个权利要求结构是否覆盖了所有创新点？
```

### Phase 3: Research Before Writing

Before writing ANY section:

**Step 3.1 — Search for related patents**

```
node scripts/search.mjs "[technology keyword] patent application" -n 5
node scripts/search.mjs "[innovation keyword] prior art" -n 5
```

**Step 3.2 — Search for GB national standards**

For Chinese patent applications, cite relevant GB (国家标准) standards:

```
node scripts/search.mjs "GB/T [领域关键词] 国家标准" -n 5
node scripts/search.mjs "[技术领域] GB标准 site:std.samr.gov.cn" -n 5
```

Also search the official standards database:
- https://std.samr.gov.cn/ (国家标准全文公开系统)
- https://openstd.samr.gov.cn/ (强制性国家标准)

GB standards add credibility and align with Chinese patent examination. Cite when:
- Describing the technical field (引用领域基础标准)
- Defining terms or metrics (引用术语/测试方法标准)
- Describing system interfaces or protocols (引用接口标准)
- Background art mentions industry norms (引用行业规范标准)

Format: `GB/T XXXXX-YYYY` (推荐性标准) 或 `GB XXXXX-YYYY` (强制性标准)

**Step 3.3 — Search for technical references**

```
node scripts/search.mjs "[technical approach] implementation" -n 5
node scripts/search.mjs "[problem being solved] existing solutions" -n 5
```

**Step 3.3 — Find real patent examples**

Use agent-browser or web search to find example patents in the same domain:
- Search Google Patents for similar patents
- Note the writing style, claim structure, description format

**Step 3.4 — Compile references**

```
## 参考资料（本节使用）

| # | 来源 | URL | 用途 |
|---|------|-----|------|
| 1 | [标题] | [完整URL] | [说明] |
| 2 | [标题] | [完整URL] | [说明] |
```

**Every reference MUST have a URL. No exceptions.**

### Phase 4: Section-by-Section Writing

#### Writing Order

Write in this order, one at a time:

1. **技术领域** (Technical Field)
2. **背景技术** (Background Art) — MUST cite real references
3. **发明内容** (Summary of Invention)
   - 技术问题 (Technical Problem)
   - 技术方案 (Technical Solution)
   - 有益效果 (Beneficial Effects)
4. **附图说明** (Description of Drawings) — with placeholders
5. **具体实施方式** (Detailed Description)
6. **权利要求书** (Claims)
7. **摘要** (Abstract)

#### For Each Section

```
1. Research → Gather sources with URLs
2. Think → Outline the section content
3. Write → Draft in Chinese (patent style)
4. Verify → Check: every claim has a source or code reference
5. Present → Show to user for approval
6. Revise → Adjust based on user feedback
7. ✅ Next section
```

#### Section Template

When presenting each section to user:

```markdown
## [章节名称] — 草稿

### 本节使用的参考资料
1. [来源1] — [URL]
2. [来源2] — [URL]

### 引用的国家标准
- GB/T XXXX-YYYY — [标准名称，用途说明]
- GB XXXX-YYYY — [标准名称，用途说明]

### 本节基于的代码依据
- [文件名:行号] — [说明]

### 正文
[草稿内容]

### 需要你确认的问题
- [问题1]
- [问题2]

请审阅并确认，或提出修改意见。
```

### Phase 5: DOCX Output

After all sections are approved:

**Step 5.1 — Write to DOCX using word-docx skill**

Template was already read in Phase 1. Now fill it in:

- Preserve all template styles
- Fill in sections according to the template structure
- For places needing diagrams, insert comment placeholders:

```markdown
[图注：此处需要插入附图N —— XXX系统架构图]
[图注：此处需要插入附图N —— XXX流程图]
```

**Step 5.3 — Verify output**

```bash
python3 -c "
from docx import Document
doc = Document('[output_path]')
print(f'段落数: {len(doc.paragraphs)}')
print(f'表格数: {len(doc.tables)}')
for p in doc.paragraphs:
    if '图注' in p.text:
        print(f'[需要图] {p.text}')
"
```

## Diagram Placeholders

Since Claude Code cannot generate patent diagrams (flowcharts, system architecture, sequence diagrams), always use structured placeholders:

```
[附图 N]
图名：[准确的图名]
类型：[流程图/系统架构图/数据流图/时序图]
内容描述：
- [元素1]：[说明]
- [元素2]：[说明]
- 连接关系：[说明]
用户需根据以上描述绘制图形。
```

## Writing Style

Patent Chinese has specific conventions:

- 使用"所述"指代前面提到的元素
- 使用"其特征在于"引出创新点
- 方法权利要求用"包括以下步骤"
- 系统权利要求用"包括以下模块/单元"
- 避免使用"本发明"以外的第一人称
- 技术术语前后一致

## Quality Checklist

Before finalizing any section:

- [ ] 每个技术论断有代码引用或网络来源
- [ ] 没有从"记忆"生成的内容
- [ ] 所有参考链接可访问
- [ ] 相关领域引用了 GB 国家标准（术语、测试方法、接口规范等）
- [ ] GB 标准编号格式正确（GB/T XXXX-YYYY）
- [ ] 权利要求语言准确、无歧义
- [ ] 技术术语全文一致
- [ ] 附图位置有清晰的占位符
- [ ] 用户已确认本节内容
