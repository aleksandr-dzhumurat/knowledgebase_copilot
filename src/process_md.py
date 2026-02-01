#!/usr/bin/env python3
"""
Script to count tokens in markdown files from interview_preparation directory.
Uses tiktoken to count tokens with the 'cl100k_base' encoding (GPT-4).
"""

from pathlib import Path
import tiktoken


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
        text = open(file_path, 'r', encoding='utf-8').read()
        token_count = len(enc.encode(text))
        return token_count
    except Exception as e:
        print(f"  ⚠️ Error processing {file_path.name}: {e}")
        return None


def main():
    """
    Main function to process all markdown files in interview_preparation directory.
    """
    # Paths setup
    ROOT_DATA_DIR = Path(__file__).parent.parent
    DATA_DIR = ROOT_DATA_DIR / "data"
    interview_dir = DATA_DIR / "interview_preparation"

    if not interview_dir.exists():
        print(f"Error: Directory not found at {interview_dir}")
        return

    # Find all markdown files
    md_files = sorted(interview_dir.glob("*.md"))

    if not md_files:
        print(f"No markdown files found in {interview_dir}")
        return

    print(f"Found {len(md_files)} markdown file(s) in {interview_dir}")
    print(f"Encoding: cl100k_base (GPT-4)")
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
    print(f"📊 Average: {total_tokens // successful_files:,} tokens per file" if successful_files > 0 else "")
    print("=" * 80)


if __name__ == "__main__":
    main()
