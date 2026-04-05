# nano-pdf — Claude Code Skill

用自然语言指令编辑 PDF 页面。

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- 已安装 Python 3 + uv 或 pip

## 安装

```bash
# 推荐用 uv
uv tool install nano-pdf

# 或用 pip
pip install nano-pdf
```

### 安装到 Claude Code

```bash
cp -r nano-pdf ~/.claude/skills/
```

## 验证

```bash
nano-pdf --help
```

## 使用方式

在 Claude Code 中直接说需要编辑 PDF，Claude 会自动调用此 skill。

### 示例

```
把第 1 页的标题改成 "Q3 财报"
修复第 3 页副标题的错别字
```

### 注意事项

- 页码可能是 0-based 或 1-based，如果结果偏移一页，换另一种试试
- 编辑后务必检查输出 PDF

## 文件结构

```
nano-pdf/
├── SKILL.md           # Claude Code 指令文件
└── README-HUMAN.md    # 本文件
```

## License

MIT
