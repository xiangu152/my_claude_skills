---
name: chm-to-md
description: Batch convert CHM files or HTML/HTM directories to Markdown (.md) format. Use when user asks to convert CHM to MD, batch convert HTML help files, extract content from .chm files, or migrate help documentation to Markdown. Requires extract_chmLib (install via `brew install chmlib` on macOS).
---

# CHM to MD Converter

Batch converts CHM help files or HTML/HTM directories to Markdown format using `extract_chmLib`.

## Prerequisites

**macOS:**
```bash
brew install chmlib
```

## Usage

### Convert a single CHM file
```bash
python scripts/convert.py /path/to/file.chm
# Output → /path/to/file_md/
```

### Convert with custom output directory
```bash
python scripts/convert.py /path/to/file.chm --output ~/Desktop/my_docs
```

### Convert a directory of HTML files
```bash
python scripts/convert.py /path/to/html_folder
```

## Workflow

1. **Extract CHM** → `extract_chmLib` decompresses the CHM (LZX-compressed HTML Help format)
2. **Find HTML** → Locate all `.htm`/`.html` files preserving directory structure
3. **Strip Tags** → Remove HTML/CSS/JS, convert `<br>`/`<p>`/`<h*>`/`<li>`/`<table>` to Markdown equivalents
4. **Unescape** → Decode HTML entities (`&nbsp;` → ` `, etc.)
5. **Write MD** → Output `.md` files in parallel directory structure

## Conversion Rules

| HTML | Markdown |
|------|----------|
| `<br>` | `\n` |
| `<p>` | `\n\n` |
| `<h1>`-`<h6>` | `## ` - `###### ` |
| `<li>` | `- ` |
| `<tr>`/`<td>` | table row/cell |
| `<style>`/`<script>` | stripped |
| HTML entities | decoded |

## Notes

- Encoding auto-detects UTF-8 → GBK fallback for Chinese docs
- Directory structure preserved under `{chm_name}_md/`
- Images and CSS files are skipped (text-only conversion)
- CHM system files (`#*`) are skipped
