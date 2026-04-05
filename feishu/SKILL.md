---
name: feishu
description: "Feishu (Lark) API operations for documents, cloud storage, permissions, wiki, and bitables. Use when: (1) reading/writing Feishu documents, (2) managing cloud drive files, (3) managing document permissions, (4) navigating wiki/knowledge base, (5) working with bitable (multidimensional tables). Triggers on 'feishu', 'lark', '飞书', 'cloud doc', 'wiki', 'bitable'. NOT for: messaging/chat (not supported), calendar, or when the task doesn't involve Feishu."
---

# Feishu

Feishu (Lark) Open API integration for documents, drive, permissions, wiki, and bitable.

## Prerequisites

1. A Feishu app with required permissions configured at https://open.feishu.cn
2. Environment variables:

```bash
export FEISHU_APP_ID="cli_xxxxx"
export FEISHU_APP_SECRET="xxxxx"
```

## Quick Start

All operations use `scripts/feishu.mjs`. Syntax:

```bash
node "$SCRIPT_DIR/scripts/feishu.mjs" <tool> <action> [params...]
```

## Authentication

The script automatically obtains and caches `tenant_access_token`. No manual token management needed.

## Tools

### feishu_doc — Document Operations

```bash
# Read document
node scripts/feishu.mjs doc read --doc_token ABC123def

# Write (replace all content with markdown)
node scripts/feishu.mjs doc write --doc_token ABC123def --content "# Title\n\nHello"

# Append content
node scripts/feishu.mjs doc append --doc_token ABC123def --content "More text"

# Create document
node scripts/feishu.mjs doc create --title "New Doc" --folder_token fldcnXXX

# List blocks
node scripts/feishu.mjs doc list_blocks --doc_token ABC123def

# Get single block
node scripts/feishu.mjs doc get_block --doc_token ABC123def --block_id doxcnXXX

# Update block text
node scripts/feishu.mjs doc update_block --doc_token ABC123def --block_id doxcnXXX --content "New text"

# Delete block
node scripts/feishu.mjs doc delete_block --doc_token ABC123def --block_id doxcnXXX

# Create table
node scripts/feishu.mjs doc create_table --doc_token ABC123def --row_size 3 --column_size 2

# Write table cells
node scripts/feishu.mjs doc write_table_cells --doc_token ABC123def --table_block_id doxcnTABLE --values '[["A1","B1"],["A2","B2"]]'

# Create table with values (one-step)
node scripts/feishu.mjs doc create_table_with_values --doc_token ABC123def --row_size 2 --column_size 2 --values '[["A1","B1"],["A2","B2"]]'

# Upload image from URL
node scripts/feishu.mjs doc upload_image --doc_token ABC123def --url "https://example.com/img.png"

# Upload image from local file
node scripts/feishu.mjs doc upload_image --doc_token ABC123def --file_path "/tmp/img.png"

# Upload file attachment
node scripts/feishu.mjs doc upload_file --doc_token ABC123def --url "https://example.com/report.pdf"

# Insert content after a block
node scripts/feishu.mjs doc insert --doc_token ABC123def --after_block_id doxcnXXX --content "Inserted text"
```

#### Token Extraction

From URL `https://xxx.feishu.cn/docx/ABC123def` → `doc_token` = `ABC123def`

#### Supported Markdown

Headings, lists, code blocks, quotes, links, images (`![](url)`), bold/italic/strikethrough.

**Limitation:** Markdown tables are NOT supported in write/append. Use `create_table_with_values` instead.

#### Block Types (reference)

| ID | Type | Editable |
|----|------|----------|
| 2 | Text | Yes |
| 3-11 | Heading1-9 | Yes |
| 12 | Bullet | Yes |
| 13 | Ordered | Yes |
| 14 | Code | Yes |
| 15 | Quote | Yes |
| 17 | Todo | Yes |
| 22 | Divider | No |
| 27 | Image | Partial |
| 31 | Table | Partial |
| 32 | TableCell | Yes |

#### Required Permissions

`docx:document`, `docx:document:readonly`, `docx:document.block:convert`, `drive:drive`

### feishu_drive — Cloud Storage

```bash
# List root folder
node scripts/feishu.mjs drive list

# List specific folder
node scripts/feishu.mjs drive list --folder_token fldcnXXX

# Get file info
node scripts/feishu.mjs drive info --file_token ABC123 --type docx

# Create folder (in parent folder — bots have no root folder!)
node scripts/feishu.mjs drive create_folder --name "New Folder" --folder_token fldcnXXX

# Move file
node scripts/feishu.mjs drive move --file_token ABC123 --type docx --folder_token fldcnXXX

# Delete file
node scripts/feishu.mjs drive delete --file_token ABC123 --type docx
```

#### File Types

`doc`, `docx`, `sheet`, `bitable`, `folder`, `file`, `mindnote`, `shortcut`

#### Known Limitation: Bots Have No Root Folder

Bots use `tenant_access_token` and don't have their own "My Space". `create_folder` without `folder_token` will fail. User must create a folder and share it with the bot first.

#### Required Permissions

`drive:drive` (full), `drive:drive:readonly` (read only)

### feishu_perm — Permission Management

```bash
# List collaborators
node scripts/feishu.mjs perm list --token ABC123 --type docx

# Add collaborator (by email)
node scripts/feishu.mjs perm add --token ABC123 --type docx --member_type email --member_id user@example.com --perm edit

# Add collaborator (by open_id)
node scripts/feishu.mjs perm add --token ABC123 --type docx --member_type openid --member_id ou_xxx --perm full_access

# Remove collaborator
node scripts/feishu.mjs perm remove --token ABC123 --type docx --member_type email --member_id user@example.com
```

#### Member Types

`email`, `openid`, `userid`, `unionid`, `openchat`, `opendepartmentid`

#### Permission Levels

`view`, `edit`, `full_access`

#### Required Permissions

`drive:permission`

### feishu_wiki — Knowledge Base

```bash
# List knowledge spaces
node scripts/feishu.mjs wiki spaces

# List nodes in space (root)
node scripts/feishu.mjs wiki nodes --space_id 7xxx

# List child nodes
node scripts/feishu.mjs wiki nodes --space_id 7xxx --parent_node_token wikcnXXX

# Get node details (returns obj_token for use with feishu_doc)
node scripts/feishu.mjs wiki get --token ABC123def

# Create node
node scripts/feishu.mjs wiki create --space_id 7xxx --title "New Page"

# Create node with type and parent
node scripts/feishu.mjs wiki create --space_id 7xxx --title "Sheet" --obj_type sheet --parent_node_token wikcnXXX

# Move node
node scripts/feishu.mjs wiki move --space_id 7xxx --node_token wikcnXXX

# Rename node
node scripts/feishu.mjs wiki rename --space_id 7xxx --node_token wikcnXXX --title "New Title"
```

#### Wiki-Doc Workflow

To edit a wiki page:
1. Get node: `wiki get --token wiki_token` → returns `obj_token`
2. Read doc: `doc read --doc_token obj_token`
3. Write doc: `doc write --doc_token obj_token --content "..."`

#### Required Permissions

`wiki:wiki` or `wiki:wiki:readonly`

### feishu_bitable — Multidimensional Tables

```bash
# Parse URL and get metadata
node scripts/feishu.mjs bitable get_meta --url "https://xxx.feishu.cn/base/XXX?table=YYY"

# List fields (columns)
node scripts/feishu.mjs bitable list_fields --app_token XXX --table_id YYY

# List records (rows)
node scripts/feishu.mjs bitable list_records --app_token XXX --table_id YYY --page_size 100

# Get single record
node scripts/feishu.mjs bitable get_record --app_token XXX --table_id YYY --record_id recXXX

# Create record
node scripts/feishu.mjs bitable create_record --app_token XXX --table_id YYY --fields '{"Name":"Test","Score":95}'

# Update record
node scripts/feishu.mjs bitable update_record --app_token XXX --table_id YYY --record_id recXXX --fields '{"Score":100}'

# Create new bitable app
node scripts/feishu.mjs bitable create_app --name "My Table" --folder_token fldcnXXX

# Create field (column)
node scripts/feishu.mjs bitable create_field --app_token XXX --table_id YYY --field_name "Status" --field_type 3
```

#### Field Types

| ID | Type |
|----|------|
| 1 | Text |
| 2 | Number |
| 3 | SingleSelect |
| 4 | MultiSelect |
| 5 | DateTime |
| 7 | Checkbox |
| 11 | User |
| 13 | Phone |
| 15 | URL |
| 17 | Attachment |
| 18 | SingleLink |
| 19 | Lookup |
| 20 | Formula |
| 1001 | CreatedTime |
| 1002 | ModifiedTime |
| 1003 | CreatedUser |
| 1004 | ModifiedUser |
| 1005 | AutoNumber |

## Tips

- Always pass `owner_open_id` when creating docs so the requester gets access
- For wiki pages, use `wiki get` to find `obj_token`, then use `doc` tools to edit content
- Bots have no root folder in drive — always specify `folder_token`
- Large documents may need `list_blocks` instead of `read` for structured content
- Use `--json` flag for raw JSON output when needed

## Output Format

All commands return JSON with the operation result. On error, returns `{ "error": "message" }`.
