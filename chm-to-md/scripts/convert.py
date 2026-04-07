#!/usr/bin/env python3
"""
CHM -> MD Batch Converter

Usage:
    python convert.py <chm_file> [--output <output_dir>]
    python convert.py <directory_with_html_files> [--output <output_dir>]
"""

import os
import re
import sys
import html
from pathlib import Path


def strip_html_tags(text):
    """Remove HTML tags, keeping content."""
    text = re.sub(r'<head[^>]*>.*?</head>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<h[1-6][^>]*>', '\n## ', text, flags=re.IGNORECASE)
    text = re.sub(r'</h[1-6]>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<li[^>]*>', '\n- ', text, flags=re.IGNORECASE)
    text = re.sub(r'</li>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<tr[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<td[^>]*>', ' | ', text, flags=re.IGNORECASE)
    text = re.sub(r'<th[^>]*>', '| ', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


def unescape_html(text):
    """Convert HTML entities to characters."""
    return html.unescape(text)


def convert_file(input_path: Path, output_path: Path):
    """Convert a single HTML/HTM file to Markdown."""
    # Try GBK first (common for Chinese CHM), then UTF-8
    for encoding in ['gbk', 'gb2312', 'utf-8']:
        try:
            content = input_path.read_text(encoding=encoding, errors='strict')
            break
        except (UnicodeDecodeError, LookupError):
            if encoding == 'utf-8':
                content = input_path.read_text(encoding='utf-8', errors='replace')

    # Unescape HTML entities first, then strip tags
    text = unescape_html(content)
    text = strip_html_tags(text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding='utf-8')
    print(f"  → {output_path.relative_to(output_path.parent)}")


def find_chm_files(root_dir: Path):
    """Find all CHM files under root_dir recursively."""
    return list(root_dir.rglob("*.chm"))


def find_html_files(root_dir: Path):
    """Find all HTML/HTM files under root_dir."""
    return list(root_dir.rglob("*.htm")) + list(root_dir.rglob("*.html"))


def process_chm(chm_path: Path, output_dir: Path):
    """Extract CHM and convert to MD."""
    import tempfile
    import subprocess

    print(f"\n📦 Extracting CHM: {chm_path.name}")

    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ['extract_chmLib', str(chm_path), tmpdir],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  ⚠️ extract_chmLib failed: {result.stderr}")
            return

        html_files = find_html_files(Path(tmpdir))
        print(f"  Found {len(html_files)} HTML files")

        for html_file in html_files:
            rel_path = html_file.relative_to(Path(tmpdir))
            md_path = output_dir / chm_path.stem / rel_path.with_suffix('.md')
            convert_file(html_file, md_path)

    print(f"  ✅ Done → {output_dir / chm_path.stem}/")


def process_directory(input_dir: Path, output_dir: Path):
    """Process a directory of HTML files."""
    html_files = find_html_files(input_dir)
    print(f"\n📂 Found {len(html_files)} HTML files in {input_dir}")

    for html_file in html_files:
        rel_path = html_file.relative_to(input_dir)
        md_path = output_dir / rel_path.with_suffix('.md')
        convert_file(html_file, md_path)

    print(f"  ✅ Done → {output_dir}/")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path = Path(sys.argv[1]).expanduser().resolve()
    
    # Parse args: handle both positional-only and --output flag
    args = sys.argv[2:]
    output_dir = None
    if '--output' in args:
        idx = args.index('--output')
        if idx + 1 < len(args):
            output_dir = Path(args[idx + 1]).expanduser().resolve()
    elif len(args) > 0 and not args[0].startswith('-'):
        output_dir = Path(args[0]).expanduser().resolve()
    
    if output_dir is None:
        output_dir = input_path.parent / f"{input_path.stem}_md"

    if not input_path.exists():
        print(f"❌ Not found: {input_path}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_file() and input_path.suffix.lower() == '.chm':
        process_chm(input_path, output_dir)
    elif input_path.is_dir():
        process_directory(input_path, output_dir)
    else:
        print(f"❌ Expected .chm file or directory: {input_path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
