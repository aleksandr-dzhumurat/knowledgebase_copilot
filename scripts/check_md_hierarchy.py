#!/usr/bin/env python3
"""
Check markdown files for heading hierarchy violations.

Example: python src/check_md_hierarchy.py docs/README.md
Validates heading hierarchy and reports violations.
"""

import argparse
import re
import sys
from pathlib import Path


def check_heading_hierarchy(file_path):
    """Check markdown file for heading hierarchy violations."""
    violations = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    prev_level = 0
    in_code_block = False

    for line_num, line in enumerate(lines, 1):
        # Track code blocks
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue

        # Skip lines inside code blocks
        if in_code_block:
            continue

        # Match headings (lines starting with #)
        heading_match = re.match(r'^(#{1,6})\s+(.+)', line)

        if heading_match:
            current_level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            # Check if level is skipped (going down)
            if current_level > prev_level + 1:
                violations.append({
                    'line': line_num,
                    'type': 'level_skip',
                    'prev_level': prev_level,
                    'current_level': current_level,
                    'text': heading_text,
                    'content': line.strip()
                })

            prev_level = current_level

        # Check for headings without spaces (but not code comments)
        no_space_match = re.match(r'^(#{1,6})([^\s#])', line)
        if no_space_match:
            violations.append({
                'line': line_num,
                'type': 'no_space',
                'content': line.strip()
            })

    return violations


def main():
    """Check markdown files for hierarchy violations."""
    parser = argparse.ArgumentParser(
        description="Check markdown files for heading hierarchy violations"
    )
    parser.add_argument(
        "file_paths",
        nargs="+",
        type=str,
        help="Path(s) to markdown file(s) to check",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Markdown Hierarchy Checker")
    print("=" * 60)
    print()

    total_violations = 0
    files_checked = 0

    for file_path in args.file_paths:
        md_file = Path(file_path)

        if not md_file.exists():
            print(f"⚠ File not found: {md_file}")
            continue

        if not md_file.suffix == '.md':
            print(f"⚠ Not a markdown file: {md_file}")
            continue

        files_checked += 1
        violations = check_heading_hierarchy(md_file)

        if violations:
            print(f"✗ {md_file.name}")
            print(f"  Found {len(violations)} violation(s):")

            for v in violations:
                if v['type'] == 'level_skip':
                    prev_h = '#' * v['prev_level'] if v['prev_level'] > 0 else 'START'
                    curr_h = '#' * v['current_level']
                    print(f"  Line {v['line']}: Level skip {prev_h} → {curr_h}")
                    print(f"    {v['content']}")
                    print(f"    Fix: Use {'#' * (v['prev_level'] + 1)} instead of {curr_h}")
                elif v['type'] == 'no_space':
                    print(f"  Line {v['line']}: Missing space after #")
                    print(f"    {v['content']}")

            print()
            total_violations += len(violations)
        else:
            print(f"✓ {md_file.name} - No violations found")
            print()

    print("=" * 60)
    if total_violations == 0:
        print(f"✓ All {files_checked} file(s) passed validation")
    else:
        print(f"✗ Found {total_violations} violation(s) in {files_checked} file(s)")
    print("=" * 60)

    sys.exit(0 if total_violations == 0 else 1)


if __name__ == "__main__":
    main()
