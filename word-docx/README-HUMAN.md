# Word / DOCX — Claude Code Skill

让 Claude Code 具备处理 Word 文档的能力，支持样式、修订、表格、目录等高级操作。

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- 已安装 Python 3 + pip

## 依赖安装

```bash
pip install python-docx lxml
```

## 安装到 Claude Code

```bash
cp -r word-docx ~/.claude/skills/
```

## 验证

```bash
python3 -c "import docx, lxml; print('OK')"
```

## 使用方式

在 Claude Code 中直接说需要操作 Word 文档，Claude 会自动调用此 skill。

### 适用场景

- 创建 Word 文档（含样式、表格、目录）
- 读取和分析现有 DOCX 文件
- 编辑模板并保留原有格式
- 处理修订模式（tracked changes）
- 处理批注、书签、交叉引用
- 处理页眉页脚、分节、页码
- 处理编号和列表

### 不适用场景

- 纯文本处理
- PDF 编辑
- 不需要保留格式的简单文档

## 工具选择指南

| 场景 | 推荐工具 |
|------|----------|
| 创建新文档 | python-docx |
| 保留格式编辑 | 直接操作 OOXML (lxml) |
| 快速文本提取 | python-docx + 提取脚本 |
| 复杂修订处理 | lxml 解析 document.xml |

## 关键注意事项

- `.docx` 是 ZIP 包含 XML，结构和可见文本同样重要
- 样式 > 直接格式化（保持可编辑性）
- 编号系统独立于文本，"看起来对"不等于"真的对"
- 页面布局在 section 级别，不在段落级别
- 跨编辑器兼容性需要验证（Word → LibreOffice → Google Docs）

## 文件结构

```
word-docx/
├── SKILL.md           # Claude Code 指令文件
└── README-HUMAN.md    # 本文件
```

## License

MIT
