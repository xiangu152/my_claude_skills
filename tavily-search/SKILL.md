---
name: tavily-search
description: Web search using Tavily's LLM-optimized API. Use when the user asks to search the web, look up information online, find recent news, or research a topic. NOT for: searching local files, code lookup, or when the answer is purely based on existing knowledge.
---

# Tavily Search

Search the web and get relevant results optimized for LLM consumption.

## Authentication

Requires the `TAVILY_API_KEY` environment variable. Get your API key at https://tavily.com.

Set it in your shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
export TAVILY_API_KEY="your-api-key-here"
```

Windows 用户：Claude Code 自带 bash，同样写入 `~/.bashrc` 即可。

## Usage

Run the search script located in this skill's `scripts/` directory. Resolve `SCRIPT` relative to this SKILL.md file.

```bash
# Basic search
node "$SCRIPT_DIR/scripts/search.mjs" "your query"

# With options
node "$SCRIPT_DIR/scripts/search.mjs" "your query" -n 10
node "$SCRIPT_DIR/scripts/search.mjs" "your query" --depth advanced
node "$SCRIPT_DIR/scripts/search.mjs" "your query" --topic news
node "$SCRIPT_DIR/scripts/search.mjs" "your query" --time-range week
node "$SCRIPT_DIR/scripts/search.mjs" "your query" --include-domains docs.python.org
node "$SCRIPT_DIR/scripts/search.mjs" "your query" --json
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `-n <count>` | Number of results (1-20) | 10 |
| `--depth <mode>` | `ultra-fast`, `fast`, `basic`, `advanced` | `basic` |
| `--topic <topic>` | `general` or `news` | `general` |
| `--time-range <range>` | `day`, `week`, `month`, `year` | - |
| `--include-domains <domains>` | Comma-separated domains to include | - |
| `--exclude-domains <domains>` | Comma-separated domains to exclude | - |
| `--raw-content` | Include full page content | false |
| `--json` | Output raw JSON | false |

## Tips

- Keep queries concise — think search query, not prompt
- Use `--depth advanced` when precision matters
- Use `--topic news` for current events
- Use `--time-range` to filter by recency
- Use `--include-domains` to focus on trusted sources
