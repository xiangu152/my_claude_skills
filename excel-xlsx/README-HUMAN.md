# Excel / XLSX — Claude Code Skill

让 Claude Code 具备处理 Excel 文件的能力，支持公式、格式、模板保护等高级操作。

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- 已安装 Python 3 + pip

## 依赖安装

```bash
pip install openpyxl pandas
```

## 安装到 Claude Code

```bash
cp -r excel-xlsx ~/.claude/skills/
```

## 验证

```bash
python3 -c "import openpyxl, pandas; print('OK')"
```

## 使用方式

在 Claude Code 中直接说需要操作 Excel 文件，Claude 会自动调用此 skill。

### 适用场景

- 创建 Excel 工作簿（含公式、格式、条件格式）
- 读取和分析现有 Excel 文件
- 编辑模板并保留原有格式
- 处理合并单元格、数据验证、打印区域
- CSV/TSV 与 Excel 互转

### 不适用场景

- 纯文本数据处理（用 pandas 即可）
- 不需要保留格式的简单 CSV 读写

## 工具选择指南

| 场景 | 推荐工具 |
|------|----------|
| 数据分析、重塑 | pandas |
| 公式、样式、合并单元格 | openpyxl |
| 保留现有工作簿格式 | openpyxl |
| 大文件流式读取 | openpyxl (read_only mode) |

## 文件结构

```
excel-xlsx/
├── SKILL.md           # Claude Code 指令文件
└── README-HUMAN.md    # 本文件
```

## License

MIT
