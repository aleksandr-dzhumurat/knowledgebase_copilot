#!/usr/bin/env python3
"""
Script to count tokens in markdown files from interview_preparation directory.
Uses tiktoken to count tokens with the 'cl100k_base' encoding (GPT-4).

uv run python src/process_md.py --md ~/Downloads/perf_engineering_course/week_01_agents_compressed_v2/week_01_agents_compressed_v2.md
✅ Read 94 slides from week_01_agents_compressed_v2.md

uv run python src/process_md.py \
    --origin ~/Downloads/perf_engineering_course/week_01_agents_compressed/week_01_agents_compressed.md \
    --candidate ~/Downloads/perf_engineering_course/week_01_agents_shrinked/week_01_agents_shrinked.md \
    --mode sparse
"""

from pathlib import Path
import tiktoken
import argparse
import re
from dataclasses import dataclass


@dataclass
class Slide:
    num: int
    body: str


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
    print(f"\n📊 Comparison Results:")
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
    parser.add_argument("--origin", type=Path, help="Path to the original markdown file for comparison")
    parser.add_argument("--candidate", type=Path, help="Path to the candidate markdown file for comparison")
    parser.add_argument("--mode", choices=["exact", "sparse"], default="exact", help="Comparison mode (default: exact)")
    args = parser.parse_args()

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
