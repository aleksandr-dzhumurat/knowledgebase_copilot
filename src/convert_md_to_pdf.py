#!/usr/bin/env python3
"""
Convert markdown files to PDF or LaTeX

Example: python src/convert_md_to_pdf.py docs/README.md notes/guide.md
Example: python src/convert_md_to_pdf.py --format tex docs/README.md
Creates output files in the same directory as the source markdown files.

Supports: headings, bold/italic, code blocks, math ($/$$), lists, links, tables
Tip: Run check_md_hierarchy.py first to validate heading structure.
"""

import argparse
import sys
from pathlib import Path

from markdown_pdf import MarkdownPdf, Section

import re


def markdown_to_latex(md_content):
    """Convert markdown content to LaTeX using basic conversion rules"""
    # Start with LaTeX document structure
    latex = []
    latex.append(r"\documentclass[12pt,a4paper]{article}")
    latex.append(r"\usepackage[utf8]{inputenc}")
    latex.append(r"\usepackage[margin=1in]{geometry}")  # Set 1 inch margins
    latex.append(r"\usepackage{amsmath}")
    latex.append(r"\usepackage{listings}")
    latex.append(r"\usepackage{xcolor}")
    latex.append(r"\usepackage{hyperref}")
    latex.append(r"\usepackage{graphicx}")
    latex.append("")
    latex.append(r"\lstset{")
    latex.append(r"  basicstyle=\ttfamily\small,")
    latex.append(r"  breaklines=true,")
    latex.append(r"  frame=single,")
    latex.append(r"  backgroundcolor=\color{gray!10}")
    latex.append(r"}")
    latex.append("")
    latex.append(r"\begin{document}")
    latex.append("")

    lines = md_content.split('\n')
    in_code_block = False
    code_lang = None
    in_list = False  # Track if we're in a list environment
    list_type = None  # Track type: 'itemize' or 'enumerate'
    in_table = False
    table_rows = []

    def close_list():
        """Helper to close an open list"""
        nonlocal in_list, list_type
        if in_list:
            if list_type == 'itemize':
                latex.append(r"\end{itemize}")
            elif list_type == 'enumerate':
                latex.append(r"\end{enumerate}")
            in_list = False
            list_type = None

    def close_table():
        """Helper to close and render table"""
        nonlocal in_table, table_rows
        if in_table and table_rows:
            # Convert table to LaTeX
            latex.extend(convert_table_to_latex(table_rows))
            in_table = False
            table_rows = []

    def convert_table_to_latex(rows):
        """Convert markdown table rows to LaTeX tabular"""
        if len(rows) < 2:
            return []

        result = []

        # Parse header and separator
        header = [cell.strip() for cell in rows[0].split('|')[1:-1]]

        # Determine alignment from separator (row 1)
        alignments = []
        sep_cells = rows[1].split('|')[1:-1]
        for cell in sep_cells:
            cell = cell.strip()
            if cell.startswith(':') and cell.endswith(':'):
                alignments.append('c')
            elif cell.endswith(':'):
                alignments.append('r')
            else:
                alignments.append('l')

        # Start table
        result.append("")
        result.append(r"\begin{table}[h]")
        result.append(r"\centering")
        result.append(r"\begin{tabular}{|" + "|".join(alignments) + "|}")
        result.append(r"\hline")

        # Header row
        header_cells = [convert_inline_formatting(cell) for cell in header]
        result.append(r"\textbf{" + r"} & \textbf{".join(header_cells) + r"} \\")
        result.append(r"\hline")

        # Data rows (skip header and separator)
        for row in rows[2:]:
            cells = [cell.strip() for cell in row.split('|')[1:-1]]
            if cells:
                converted_cells = [convert_inline_formatting(cell) for cell in cells]
                result.append(" & ".join(converted_cells) + r" \\")
                result.append(r"\hline")

        result.append(r"\end{tabular}")
        result.append(r"\end{table}")
        result.append("")

        return result

    for line in lines:
        # Code blocks
        if line.strip().startswith('```'):
            if not in_code_block:
                # Start code block
                code_lang = line.strip()[3:].strip() or 'text'
                latex.append(f"\\begin{{lstlisting}}[language={code_lang}]")
                in_code_block = True
            else:
                # End code block
                latex.append(r"\end{lstlisting}")
                in_code_block = False
                code_lang = None
            continue

        if in_code_block:
            latex.append(line)
            continue

        # Tables - detect by pipe character
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                close_list()
                in_table = True
            table_rows.append(line.strip())
            continue
        else:
            # Not a table line - close table if one was open
            if in_table:
                close_table()

        # Headings
        if line.startswith('# '):
            close_list()
            text = line[2:].strip()
            text = escape_latex(text)
            latex.append(f"\\section{{{text}}}")
        elif line.startswith('## '):
            close_list()
            text = line[3:].strip()
            text = escape_latex(text)
            latex.append(f"\\subsection{{{text}}}")
        elif line.startswith('### '):
            close_list()
            text = line[4:].strip()
            text = escape_latex(text)
            latex.append(f"\\subsubsection{{{text}}}")
        elif line.startswith('#### '):
            close_list()
            text = line[5:].strip()
            text = escape_latex(text)
            latex.append(f"\\paragraph{{{text}}}")
        # Horizontal rule
        elif line.strip() == '---':
            close_list()
            latex.append(r"\hrule")
        # Unordered list
        elif line.strip().startswith('- '):
            text = line.strip()[2:]
            text = convert_inline_formatting(text)
            if not in_list or list_type != 'itemize':
                close_list()
                latex.append(r"\begin{itemize}")
                in_list = True
                list_type = 'itemize'
            latex.append(f"\\item {text}")
        # Ordered list
        elif re.match(r'^\d+\.\s', line.strip()):
            text = re.sub(r'^\d+\.\s', '', line.strip())
            text = convert_inline_formatting(text)
            if not in_list or list_type != 'enumerate':
                close_list()
                latex.append(r"\begin{enumerate}")
                in_list = True
                list_type = 'enumerate'
            latex.append(f"\\item {text}")
        # Empty line - close lists if open
        elif line.strip() == '':
            close_list()
            latex.append("")
        # Regular paragraph
        else:
            close_list()
            text = convert_inline_formatting(line)
            latex.append(text)

    # Close any open lists or tables at end
    close_list()
    close_table()

    latex.append("")
    latex.append(r"\end{document}")

    return '\n'.join(latex)


def escape_latex(text):
    """Escape special LaTeX characters"""
    # IMPORTANT: Backslash must be replaced FIRST before other chars
    # that introduce backslashes in their replacements
    text = text.replace('\\', r'\textbackslash{}')

    # Now replace other special characters
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


def convert_inline_formatting(text):
    """Convert inline markdown formatting to LaTeX"""
    # First, protect inline math: $...$
    math_placeholders = []
    def replace_math(match):
        placeholder = f"MATHPLACEHOLDER{len(math_placeholders)}ENDMATH"
        math_placeholders.append(match.group(0))  # Keep the $ signs
        return placeholder

    text = re.sub(r'\$([^\$]+)\$', replace_math, text)

    # Process inline elements by splitting and converting
    result = []

    # Process bold: **text** (must come before italic to avoid conflicts)
    parts = re.split(r'(\*\*.*?\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            content = part[2:-2]
            result.append(f"\\textbf{{{escape_latex(content)}}}")
        else:
            # Process italic: *text*
            italic_parts = re.split(r'(\*.*?\*)', part)
            for ipart in italic_parts:
                if ipart.startswith('*') and ipart.endswith('*') and not ipart.startswith('**'):
                    content = ipart[1:-1]
                    result.append(f"\\textit{{{escape_latex(content)}}}")
                else:
                    # Process inline code: `code`
                    code_parts = re.split(r'(`.*?`)', ipart)
                    for cpart in code_parts:
                        if cpart.startswith('`') and cpart.endswith('`'):
                            content = cpart[1:-1]
                            result.append(f"\\texttt{{{escape_latex(content)}}}")
                        else:
                            # Process links: [text](url)
                            link_parts = re.split(r'(\[.*?\]\(.*?\))', cpart)
                            for lpart in link_parts:
                                if lpart.startswith('[') and ')' in lpart:
                                    match = re.match(r'\[(.*?)\]\((.*?)\)', lpart)
                                    if match:
                                        link_text, url = match.groups()
                                        result.append(f"\\href{{{url}}}{{{escape_latex(link_text)}}}")
                                    else:
                                        result.append(escape_latex(lpart))
                                else:
                                    result.append(escape_latex(lpart))

    final_text = ''.join(result)

    # Restore math placeholders
    for i, math_expr in enumerate(math_placeholders):
        final_text = final_text.replace(f"MATHPLACEHOLDER{i}ENDMATH", math_expr)

    return final_text


def convert_md_to_tex(md_file_path):
    """Convert a single markdown file to LaTeX"""
    md_path = Path(md_file_path)
    tex_path = md_path.with_suffix(".tex")

    print(f"Converting: {md_path.name} -> {tex_path.name}")

    try:
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        # Convert to LaTeX
        latex_content = markdown_to_latex(md_content)

        # Write to .tex file
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        print(f"✓ Successfully created: {tex_path.name}")
        return True
    except Exception as e:
        print(f"✗ Error converting {md_path.name}: {e}")
        return False


def convert_md_to_pdf(md_file_path):
    """Convert a single markdown file to PDF"""
    md_path = Path(md_file_path)
    pdf_path = md_path.with_suffix(".pdf")

    print(f"Converting: {md_path.name} -> {pdf_path.name}")

    try:
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        pdf = MarkdownPdf()
        pdf.add_section(Section(md_content))
        pdf.save(str(pdf_path))

        print(f"✓ Successfully created: {pdf_path.name}")
        return True
    except Exception as e:
        print(f"✗ Error converting {md_path.name}: {e}")
        return False


def main():
    """Convert markdown files to PDF or LaTeX from CLI arguments"""
    parser = argparse.ArgumentParser(
        description="Convert markdown files to PDF or LaTeX"
    )
    parser.add_argument(
        "file_paths",
        nargs="+",
        type=str,
        help="Path(s) to markdown file(s) to convert",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["pdf", "tex"],
        default="pdf",
        help="Output format: pdf (default) or tex (LaTeX)",
    )

    args = parser.parse_args()

    # Select conversion function based on format
    if args.format == "tex":
        convert_func = convert_md_to_tex
        format_name = "LaTeX"
    else:
        convert_func = convert_md_to_pdf
        format_name = "PDF"

    print("=" * 60)
    print(f"Markdown to {format_name} Conversion")
    print("=" * 60)
    print()

    success_count = 0
    fail_count = 0

    for file_path in args.file_paths:
        md_file = Path(file_path)
        if md_file.exists():
            if convert_func(md_file):
                success_count += 1
            else:
                fail_count += 1
        else:
            print(f"⚠ File not found: {md_file}")
            fail_count += 1
        print()

    print("=" * 60)
    print(f"Conversion Complete: {success_count} successful, {fail_count} failed")
    print("=" * 60)

    # Exit with error code if any conversions failed
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
