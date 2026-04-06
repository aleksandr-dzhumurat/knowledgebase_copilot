#!/usr/bin/env python3
"""
TF-IDF based document index for markdown files.

Usage:
    uv run python scripts/retrieval.py --md path/to/file.md --query "your search query"
    uv run python scripts/retrieval.py --md path/to/file.md --query "fine-tuning" --top-k 3
"""

import argparse
import re
import sys
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, str(Path(__file__).parent))
from process_md import DocumentNode, read_md_nodes

_BOLD = "\033[1m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"
_CONTEXT = 40  # chars around the match


def _highlight_snippet(body: str, query: str) -> str:
    """Return a snippet of body with query terms highlighted, centred on the first match."""
    terms = [re.escape(t) for t in query.split() if t]
    pattern = re.compile("|".join(terms), re.IGNORECASE)

    flat = body.replace("\n", " ")
    m = pattern.search(flat)
    if not m:
        # No keyword found — return plain head
        return flat[:_CONTEXT * 2]

    start = max(0, m.start() - _CONTEXT)
    end = min(len(flat), m.end() + _CONTEXT)
    snippet = flat[start:end]

    # Highlight every term occurrence inside the snippet
    highlighted = pattern.sub(
        lambda hit: f"{_BOLD}{_YELLOW}{hit.group()}{_RESET}", snippet
    )
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(flat) else ""
    return prefix + highlighted + suffix


class DocumentIndex:
    def __init__(self, nodes: list[DocumentNode]):
        self._nodes = nodes
        self._vectorizer = TfidfVectorizer()
        corpus = [f"{node.header}\n{node.body}" for node in nodes]
        self._matrix = self._vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 5) -> tuple[list[tuple[float, DocumentNode]], int]:
        """Return (top_k results, total above-zero count) ranked by TF-IDF cosine similarity."""
        query_vec = self._vectorizer.transform([query])
        scores = (self._matrix @ query_vec.T).toarray().flatten()
        total_nonzero = int((scores > 0).sum())
        top_indices = scores.argsort()[::-1][:top_k]
        results = [(float(scores[i]), self._nodes[i]) for i in top_indices if scores[i] > 0]
        return results, total_nonzero

    @classmethod
    def from_md_file(cls, file_path: Path) -> "DocumentIndex":
        """Factory: build a DocumentIndex from a markdown file."""
        nodes = read_md_nodes(file_path)
        if not nodes:
            raise ValueError(f"No nodes parsed from {file_path}")
        return cls(nodes)


def main():
    parser = argparse.ArgumentParser(description="TF-IDF search over markdown document nodes")
    parser.add_argument("--md", type=Path, required=True, help="Path to markdown file")
    parser.add_argument("--query", type=str, required=True, help="Search query")
    parser.add_argument("--top-k", type=int, default=5, dest="top_k", help="Number of results (default: 5)")
    args = parser.parse_args()

    index = DocumentIndex.from_md_file(args.md)
    results, total = index.search(args.query, top_k=args.top_k)

    if not results:
        print("No matching nodes found.")
        return

    print(f"Top {len(results)} results from {total} for: \"{args.query}\"\n")
    for rank, (score, node) in enumerate(results, 1):
        print(f"{rank}. [{score:.4f}] {node.header}")
        if node.body:
            snippet = _highlight_snippet(node.body, args.query)
            print(f"   {snippet}")
        print()


if __name__ == "__main__":
    main()
