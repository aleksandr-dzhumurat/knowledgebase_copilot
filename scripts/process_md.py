#!/usr/bin/env python3
"""
Script to count tokens in markdown files from interview_preparation directory.
Uses tiktoken to count tokens with the 'cl100k_base' encoding (GPT-4).

uv run python scripts/process_md.py --md ~/Downloads/perf_engineering_course/week_01_agents_compressed_v2/week_01_agents_compressed_v2.md
✅ Read 94 slides from week_01_agents_compressed_v2.md

uv run python scripts/process_md.py \
    --origin ~/Downloads/perf_engineering_course/week_01_agents_compressed/week_01_agents_compressed.md \
    --candidate ~/Downloads/perf_engineering_course/week_01_agents_shrinked/week_01_agents_shrinked.md \
    --mode sparse
"""

import argparse
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import tiktoken


@dataclass
class Slide:
    num: int
    body: str


@dataclass
class DocumentNode:
    header: str
    body: str
    parent: "DocumentNode | None" = None
    node_name: str = field(init=False)

    def __post_init__(self):
        self.node_name = hashlib.md5((self.header + self.body).encode()).hexdigest()


def is_duplicate(body1: str, body2: str, mode: str = "exact") -> bool:
    """Check if two slide bodies are duplicates using the specified mode."""
    if mode == "sparse":
        # Compare sets of unique words (split by whitespace/newline)
        return set(body1.split()) == set(body2.split())
    # Default: exact string comparison
    return body1 == body2


def run_deduplication(origin_slides: list[Slide], candidate_slides: list[Slide], mode: str) -> int:
    """Run deduplication logic and return the count of duplicates."""
    duplicate_count = 0
    for o_slide in origin_slides:
        for c_slide in candidate_slides:
            if is_duplicate(o_slide.body, c_slide.body, mode=mode):
                duplicate_count += 1
                break
    return duplicate_count


def print_comparison_results(origin_name: str, origin_count: int, candidate_name: str, candidate_count: int, duplicate_count: int):
    """Print the results of the slide comparison."""
    print(f"Loaded {origin_count:4} slides from origin: {origin_name}")
    print(f"Loaded {candidate_count:4} slides from candidate: {candidate_name}")
    print("\n📊 Comparison Results:")
    print(f"  Duplicates found: {duplicate_count:4}")


def read_md_slides(file_path: Path) -> list[Slide]:
    """Read a markdown file and split it into Slide objects."""
    if not file_path.exists():
        print(f"Error: File not found at {file_path}")
        return []
    
    content = file_path.read_text(encoding="utf-8")
    # Split by the separator used in pdf_to_md.py
    raw_slides = content.split("\n\n---\n\n")
    
    slides = []
    for raw in raw_slides:
        raw = raw.strip()
        if not raw:
            continue
            
        # Match "## Slide 123" at the beginning, followed by newline(s)
        match = re.match(r"## Slide (\d+)\n*(.*)", raw, re.DOTALL)
        if match:
            num = int(match.group(1))
            body = match.group(2).strip()
            slides.append(Slide(num=num, body=body))
        else:
            # Fallback if header is missing
            slides.append(Slide(num=len(slides) + 1, body=raw))
            
    return slides


def _header_level(header: str) -> int:
    """Return the depth of a markdown header (number of leading #)."""
    m = re.match(r'^(#+)', header)
    return len(m.group(1)) if m else 0


def _parse_sections(content: str) -> list[tuple[int, str, str]]:
    """
    Parse markdown content into sections, skipping headers inside fenced code blocks.
    Returns [(line_num, header_line, body_text), ...].
    """
    sections: list[tuple[int, str, str]] = []
    in_code_block = False
    current_header: str | None = None
    current_line_num = 0
    body_lines: list[str] = []

    for line_num, line in enumerate(content.splitlines(keepends=True), 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if current_header is not None:
                body_lines.append(line)
            continue

        if not in_code_block and re.match(r"^#{1,6}\s+", line):
            if current_header is not None:
                sections.append((current_line_num, current_header, "".join(body_lines).strip()))
            current_header = line.rstrip()
            current_line_num = line_num
            body_lines = []
        else:
            if current_header is not None:
                body_lines.append(line)

    if current_header is not None:
        sections.append((current_line_num, current_header, "".join(body_lines).strip()))

    return sections


def check_heading_hierarchy(file_path) -> list[dict]:
    """Check markdown file for heading hierarchy violations."""
    violations = []
    content = Path(file_path).read_text(encoding="utf-8")

    # level_skip check — uses _parse_sections to respect code blocks
    prev_level = 0
    for line_num, header_line, _ in _parse_sections(content):
        current_level = _header_level(header_line)
        heading_text = re.match(r"^#{1,6}\s+(.+)", header_line).group(1).strip()
        if current_level > prev_level + 1:
            violations.append({
                "line": line_num,
                "type": "level_skip",
                "prev_level": prev_level,
                "current_level": current_level,
                "text": heading_text,
                "content": header_line,
            })
        prev_level = current_level

    # no_space check (##word without space) — separate pass, also skips code blocks
    in_code_block = False
    for line_num, line in enumerate(content.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block and re.match(r"^(#{1,6})([^\s#])", line):
            violations.append({"line": line_num, "type": "no_space", "content": line.strip()})

    return violations


def read_md_nodes(file_path: Path) -> list[DocumentNode]:
    """Read a markdown file and return a list of DocumentNode, one per header section."""
    if not file_path.exists():
        print(f"Error: File not found at {file_path}")
        return []

    content = file_path.read_text(encoding="utf-8")
    nodes = [
        DocumentNode(header=header_line, body=body)
        for _, header_line, body in _parse_sections(content)
    ]

    # --- fill parent attributes ---
    parent_level: int = 0
    parent_node: DocumentNode | None = None
    previous_level: int = 0
    previous_node: DocumentNode | None = None

    for node in nodes:
        current_level = _header_level(node.header)

        if parent_level > 0:
            diff = current_level - parent_level
            if diff == 1:
                # one level below parent → direct child
                node.parent = parent_node
            elif diff >= 2:
                # two or more levels below parent: previous node is the
                # missing intermediate level, promote it to parent
                parent_level = previous_level
                parent_node = previous_node
                node.parent = parent_node
            # diff <= 0: same level or going up → no parent, will reset below

        previous_level = current_level
        previous_node = node
        parent_level = current_level
        parent_node = node

    return nodes


def count_tokens_in_file(file_path, encoding_name="cl100k_base"):
    """
    Count tokens in a file using tiktoken.

    Args:
        file_path: Path to the file
        encoding_name: Name of the encoding to use (default: "cl100k_base")

    Returns:
        Number of tokens in the file
    """
    try:
        enc = tiktoken.get_encoding(encoding_name)
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return len(enc.encode(text))
    except (OSError, UnicodeDecodeError) as e:
        print(f"  ⚠️ Error processing {file_path.name}: {e}")
        return None


def main():
    """
    Main function to process markdown files for token counting or slide splitting.
    """
    parser = argparse.ArgumentParser(description="Process markdown files for token counting and slide splitting")
    parser.add_argument("--md", type=Path, help="Path to markdown file to read and count slides")
    parser.add_argument("--nodes", type=Path, help="Path to markdown file to read as DocumentNode list")
    parser.add_argument("--check-md", type=Path, dest="check_md", help="Check markdown file for heading hierarchy violations")
    parser.add_argument("--origin", type=Path, help="Path to the original markdown file for comparison")
    parser.add_argument("--candidate", type=Path, help="Path to the candidate markdown file for comparison")
    parser.add_argument("--mode", choices=["exact", "sparse"], default="exact", help="Comparison mode (default: exact)")
    args = parser.parse_args()

    if args.check_md:
        md_file = args.check_md
        if not md_file.exists():
            print(f"⚠ File not found: {md_file}")
            return
        violations = check_heading_hierarchy(md_file)
        if violations:
            print(f"✗ {md_file.name} — {len(violations)} violation(s):")
            for v in violations:
                if v["type"] == "level_skip":
                    prev_h = "#" * v["prev_level"] if v["prev_level"] > 0 else "START"
                    curr_h = "#" * v["current_level"]
                    print(f"  Line {v['line']}: level skip {prev_h} → {curr_h}  {v['content']}")
                    print(f"    Fix: use {'#' * (v['prev_level'] + 1)} instead of {curr_h}")
                elif v["type"] == "no_space":
                    print(f"  Line {v['line']}: missing space after #  {v['content']}")
        else:
            print(f"✓ {md_file.name} — no violations")
        return

    if args.origin and args.candidate:
        origin_slides = read_md_slides(args.origin)
        candidate_slides = read_md_slides(args.candidate)
        duplicate_count = run_deduplication(origin_slides, candidate_slides, args.mode)
        
        print_comparison_results(
            args.origin.name, len(origin_slides), 
            args.candidate.name, len(candidate_slides), 
            duplicate_count
        )
        return

    if args.nodes:
        nodes = read_md_nodes(args.nodes)
        print(f"✅ Read {len(nodes)} nodes from {args.nodes.name}")
        if nodes:
            print("\n" + "=" * 40)
            print("SAMPLE: Node 1")
            print("-" * 40)
            print(f"Header: {nodes[3].header}")
            print(f"Body:   {nodes[3].body[:300]}")
            print("=" * 40)
        return

    if args.md:
        slides = read_md_slides(args.md)
        print(f"✅ Read {len(slides)} slides from {args.md.name}")
        if slides:
            print("\n" + "=" * 40)
            print("SAMPLE: Slide 1 Body")
            print("-" * 40)
            print(slides[0].body)
            print("=" * 40)
        return

    # Paths setup
    root_data_dir = Path(__file__).parent.parent
    data_dir = root_data_dir / "data"
    interview_dir = data_dir / "interview_preparation"

    if not interview_dir.exists():
        print(f"Error: Directory not found at {interview_dir}")
        return

    # Find all markdown files
    md_files = sorted(interview_dir.glob("*.md"))

    if not md_files:
        print(f"No markdown files found in {interview_dir}")
        return

    print(f"Found {len(md_files)} markdown file(s) in {interview_dir}")
    print("Encoding: cl100k_base (GPT-4)")
    print("=" * 80)
    print()

    total_tokens = 0
    successful_files = 0

    # Process each markdown file
    for md_file in md_files:
        token_count = count_tokens_in_file(md_file)

        if token_count is not None:
            print(f"📄 {md_file.name:40s} → {token_count:6,} tokens")
            total_tokens += token_count
            successful_files += 1
        else:
            print(f"📄 {md_file.name:40s} → ERROR")

    print()
    print("=" * 80)
    print(f"✅ Total: {total_tokens:,} tokens across {successful_files} file(s)")
    print(
        f"📊 Average: {total_tokens // successful_files:,} tokens per file"
        if successful_files > 0
        else ""
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
