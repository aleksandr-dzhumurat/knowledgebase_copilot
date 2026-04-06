#!/usr/bin/env python3
"""
TF-IDF based document index for markdown files.

Usage:
    uv run python scripts/retrieval.py --md path/to/file.md --query "your search query"
    uv run python scripts/retrieval.py --md path/to/file.md --query "fine-tuning" --top-k 3
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from utils.formatting import print_search_results
from utils.retrieve import DocumentIndex

__all__ = ["DocumentIndex"]


def main():
    parser = argparse.ArgumentParser(description="TF-IDF search over markdown document nodes")
    parser.add_argument("--md", type=Path, required=True, help="Path to markdown file")
    parser.add_argument("--query", type=str, required=True, help="Search query")
    parser.add_argument("--top-k", type=int, default=5, dest="top_k", help="Number of results (default: 5)")
    args = parser.parse_args()

    if args.md.is_dir():
        index = DocumentIndex.from_dir(args.md)
    else:
        index = DocumentIndex.from_md_file(args.md)
    results, total = index.search(args.query, top_k=args.top_k)

    if not results:
        print("No matching nodes found.")
        return

    print(f"Top {len(results)} results from {total} for: \"{args.query}\"\n")
    print_search_results(results, args.query)


if __name__ == "__main__":
    main()
