#!/usr/bin/env python3
"""
Text Merger - Merges recognized speech text files into a single file.
"""

import argparse
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def text_file_iterator(prefix: str):
    """Iterate over .txt files from recognized_speech directory matching prefix.

    Args:
        prefix: Filter files that contain this prefix in the filename.

    Yields:
        Path objects for each .txt file, sorted by name.
    """
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data" / "recognized_speech"

    for txt_file in sorted(data_dir.glob("*.txt")):
        if prefix in txt_file.name:
            yield txt_file


def merge_files(prefix: str) -> Path:
    """Merge all text files matching prefix into a single file.

    Args:
        prefix: Filter files that contain this prefix in the filename.

    Returns:
        Path to the merged output file.
    """
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "data" / "recognized_speech"
    output_file = output_dir / f"{prefix}_merged.txt"

    merged_content = []
    for f in text_file_iterator(prefix):
        print(f"Adding: {f.name}")
        content = f.read_text(encoding="utf-8")
        merged_content.append(f"# {f.stem}\n\n{content}")

    output_file.write_text("\n\n---\n\n".join(merged_content), encoding="utf-8")
    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge recognized speech text files")
    parser.add_argument(
        "--prefix", required=True, help="Filter files containing this prefix in filename"
    )
    args = parser.parse_args()

    output = merge_files(args.prefix)
    print(f"Merged to: {output}")
