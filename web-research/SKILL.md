---
name: web-research
description: "Web 研究工具：搜索多个来源、综合发现并生成带引用的研究报告。用于用户要求在线研究主题、搜索网页、查找信息、获取最新信息、对比选项或生成研究报告。触发词：研究、网上搜索、查找信息、最新信息、对比选项、研究报告。"
---

# Web Research Skill

## 研究流程

### Step 1: 创建并保存研究计划

在委托给子代理之前，**必须**：

1. **创建研究文件夹** - 在相对于当前工作目录的专用文件夹中组织所有研究文件：
   ```
   mkdir research_[topic_name]
   ```
   这样可以保持文件有序，避免工作目录混乱。

2. **分析研究问题** - 将其分解为不同的、不重叠的子主题

3. **编写研究计划文件** - 使用 `write_file` 工具创建 `research_[topic_name]/research_plan.md`，包含：
   - 主要研究问题
   - 2-5 个具体的子主题
   - 每个子主题的预期信息
   - 结果如何综合

**计划指南：**
- **简单的事实查找**：1-2 个子主题
- **对比分析**：每个对比元素 1 个子主题（最多 3 个）
- **复杂调查**：3-5 个子主题

### Step 2: 委托给研究子代理

对于计划中的每个子主题：

1. **使用 `task` 工具** 生成研究子代理，包含：
   - 清晰的、具体的研究问题（无缩写）
   - 指示将发现写入文件：`research_[topic_name]/findings_[subtopic].md`
   - 预算：最多 3-5 次网络搜索

2. **最多并行运行 3 个子代理** 以提高研究效率

**子代理指令模板：**
```
Research [SPECIFIC TOPIC]. Use the web_search tool to gather information.
After completing your research, use write_file to save your findings to research_[topic_name]/findings_[subtopic].md.
Include key facts, relevant quotes, and source URLs.
Use 3-5 web searches maximum.
```

### Step 3: 综合发现

所有子代理完成后：

1. **查看发现的文件**：
   - 首先运行 `list_files research_[topic_name]` 查看创建了哪些文件
   - 然后使用 `read_file` 读取**文件路径**（例如 `research_[topic_name]/findings_*.md`）
   - **重要**：对本地文件使用 `read_file`，不是 URL

2. **综合信息** - 创建综合响应：
   - 直接回答原始问题
   - 整合所有子主题的洞察
   - 用具体来源和 URL 引用
   - 识别任何差距或局限性

3. **编写最终报告**（可选）- 如果需要，使用 `write_file` 创建 `research_[topic_name]/research_report.md`

**注意**：如果需要从 URL 获取其他信息，使用 `fetch_url` 工具，不是 `read_file`。

## 最佳实践

- **先计划后委托** - 始终先写 research_plan.md
- **清晰的子主题** - 确保每个子代理有 distinct、不重叠的范围
- **基于文件的通信** - 让子代理将发现保存到文件，而非直接返回
- **系统化综合** - 在创建最终响应前阅读所有发现文件
- **适时停止** - 不要过度研究；每个子主题 3-5 次搜索通常足够
