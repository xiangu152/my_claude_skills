# SSH Essentials — Claude Code Skill

让 Claude Code 具备 SSH 知识库，覆盖连接、密钥管理、端口转发、文件传输等常用操作。

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- 系统已安装 OpenSSH（macOS/Linux 自带）

## 安装到 Claude Code

```bash
cp -r ssh-essentials ~/.claude/skills/
```

## 使用方式

在 Claude Code 中直接问 SSH 相关问题，Claude 会自动调用此 skill。

### 覆盖场景

- SSH 连接和认证
- 密钥生成和管理
- SSH Agent 使用
- 端口转发（本地/远程/SOCKS）
- `~/.ssh/config` 配置
- 文件传输（SCP/SFTP/rsync）
- 安全加固
- 故障排查
- 跳板机（ProxyJump）
- 连接复用（Multiplexing）

## 文件结构

```
ssh-essentials/
├── SKILL.md           # Claude Code 指令文件
└── README-HUMAN.md    # 本文件
```

## License

MIT
