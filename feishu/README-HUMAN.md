# 飞书 (Feishu) — Claude Code Skill

让 Claude Code 具备飞书 Open API 操作能力，覆盖文档、云盘、权限、知识库、多维表格。

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- 已安装 Node.js
- 已创建飞书应用并获取 App ID 和 App Secret：https://open.feishu.cn

### 所需权限

根据使用的功能，在飞书开放平台申请以下权限：

| 功能 | 所需权限 |
|------|----------|
| 文档读写 | `docx:document`, `docx:document:readonly`, `docx:document.block:convert` |
| 云盘管理 | `drive:drive`, `drive:drive:readonly` |
| 权限管理 | `drive:permission` |
| 知识库 | `wiki:wiki`, `wiki:wiki:readonly` |
| 多维表格 | `bitable:app` |

## 安装

### 设置环境变量

```bash
echo 'export FEISHU_APP_ID="cli_xxxxx"' >> ~/.zshrc
echo 'export FEISHU_APP_SECRET="xxxxx"' >> ~/.zshrc
source ~/.zshrc
```

### 安装到 Claude Code

```bash
cp -r feishu ~/.claude/skills/
```

## 验证

```bash
node ~/.claude/skills/feishu/scripts/feishu.mjs --help
```

## 使用方式

在 Claude Code 中直接说需要操作飞书，Claude 会自动调用此 skill。

### 支持的功能

| 工具 | 功能 |
|------|------|
| `doc` | 文档读写、创建、块操作、表格、图片上传 |
| `drive` | 云盘文件列表、信息、创建文件夹、移动、删除 |
| `perm` | 权限管理：查看、添加、移除协作者 |
| `wiki` | 知识库：空间列表、节点操作、创建、移动、重命名 |
| `bitable` | 多维表格：字段、记录 CRUD、创建应用 |

### Token 提取

从 URL 提取 token：
- 文档：`https://xxx.feishu.cn/docx/ABC123def` → `ABC123def`
- 文件夹：`https://xxx.feishu.cn/drive/folder/ABC123` → `ABC123`
- 知识库：`https://xxx.feishu.cn/wiki/ABC123def` → `ABC123def`
- 多维表格：`https://xxx.feishu.cn/base/XXX?table=YYY` → `app_token=XXX, table_id=YYY`

## 文件结构

```
feishu/
├── SKILL.md           # Claude Code 指令文件
├── README-HUMAN.md    # 本文件
└── scripts/
    └── feishu.mjs     # 飞书 API 封装脚本
```

## 基于

OpenClaw 飞书扩展能力，去除网关/消息/定时任务相关功能，保留文档/云盘/权限/知识库/多维表格。

## License

MIT
