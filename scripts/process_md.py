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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from utils.retrieve import (
    DocumentNode,
    Slide,
    check_heading_hierarchy,
    count_tokens_in_file,
    is_duplicate,
    print_comparison_results,
    read_md_nodes,
    read_md_slides,
    run_deduplication,
)

__all__ = [
    "DocumentNode",
    "Slide",
    "check_heading_hierarchy",
    "count_tokens_in_file",
    "is_duplicate",
    "print_comparison_results",
    "read_md_nodes",
    "read_md_slides",
    "run_deduplication",
]


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
