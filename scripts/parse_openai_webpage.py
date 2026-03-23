#!/usr/bin/env python3
"""
Parse ChatGPT conversation exports (MHTML) into Q&A JSONL datasets.

Use case:
    Export a ChatGPT conversation from the browser (Save Page As → Web Page, Complete),
    place the resulting .mhtml files in a subdirectory under data/, then run:

        python src/parse_openai_webpage.py <dir_name>

    where <dir_name> is the subdirectory name relative to data/.
    Each .mhtml file produces a corresponding .jsonl file in the same directory,
    with one {"question": ..., "answer": ...} record per user/assistant exchange.

Example:
    # Save ChatGPT pages to data/my_chats/, then:
    python src/parse_openai_webpage.py my_chats
    # Output: data/my_chats/conversation_1.jsonl, ...
"""

import argparse
import email
import json
import quopri
import re
from email import policy
from pathlib import Path

from bs4 import BeautifulSoup


def extract_html_from_mhtml(mhtml_path):
    """
    Extract HTML content from an MHTML file.

    Args:
        mhtml_path: Path to the MHTML file

    Returns:
        HTML content as string, or None if not found
    """
    with open(mhtml_path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    # Extract HTML content from multipart message
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            # Check the encoding type
            encoding = part.get("Content-Transfer-Encoding", "").lower()

            if encoding == "quoted-printable":
                # Get raw payload and decode quoted-printable manually
                payload = part.get_payload(decode=False)
                if isinstance(payload, str):
                    payload = payload.encode("utf-8")
                decoded = quopri.decodestring(payload)
                return decoded.decode("utf-8", errors="replace")
            else:
                # For other encodings, use default decoding
                content = part.get_content()
                if isinstance(content, bytes):
                    return content.decode("utf-8", errors="replace")
                return content

    return None


def iterate_conversation_blocks(mhtml_path):
    """
    Iterate over conversation blocks in a ChatGPT MHTML export.

    Each block is an <article> element representing either a user message
    or an assistant response.

    Args:
        mhtml_path: Path to the MHTML file

    Yields:
        Tuple of (block_index, speaker, text_content, article_element)
        where speaker is either 'user' or 'assistant'
    """
    html_content = extract_html_from_mhtml(mhtml_path)

    if not html_content:
        print(f"No HTML content found in {mhtml_path}")
        return

    soup = BeautifulSoup(html_content, "html.parser")

    # Find all article elements - these represent conversation blocks
    articles = soup.find_all("article")

    for idx, article in enumerate(articles):
        # Extract speaker from data-turn attribute
        speaker = article.get("data-turn", "unknown")

        # Get the text content with separator to avoid word concatenation
        # Using ' ' as separator ensures words from different elements don't merge
        text = article.get_text(separator=" ", strip=True)

        # Clean up the "You said:" and "ChatGPT said:" prefixes
        if text.startswith("You said:"):
            text = text[len("You said:") :].strip()
        elif text.startswith("ChatGPT said:"):
            text = text[len("ChatGPT said:") :].strip()

        # Clean up multiple consecutive spaces
        text = re.sub(r"\s+", " ", text)

        yield idx, speaker, text, article


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Process MHTML files exported from ChatGPT conversations."
    )
    parser.add_argument(
        "dir_name",
        help="Directory name containing MHTML files (relative to data/)",
    )
    return parser.parse_args()


def main():
    """
    Main function to process all MHTML files and print conversation blocks.
    Each MHTML file produces a corresponding .jsonl file with Q&A pairs.
    """
    args = parse_args()

    # Paths setup
    ROOT_DATA_DIR = Path(__file__).parent.parent
    DATA_DIR = ROOT_DATA_DIR / "data"
    qa_dir = DATA_DIR / args.dir_name

    if not qa_dir.exists():
        print(f"Error: Directory not found at {qa_dir}")
        return

    # Find all MHTML files in the qa_knowledgebase directory
    mhtml_files = sorted(qa_dir.glob("*.mhtml"))

    if not mhtml_files:
        print(f"No MHTML files found in {qa_dir}")
        return

    print(f"Found {len(mhtml_files)} MHTML file(s) in {qa_dir}")
    print("=" * 80)
    print()

    total_qa_pairs = 0

    # Process each MHTML file
    for file_num, mhtml_file in enumerate(mhtml_files, 1):
        output_file = mhtml_file.with_suffix('.jsonl')

        print(f"\n{'='*80}")
        print(f"Processing file {file_num}/{len(mhtml_files)}: {mhtml_file.name}")
        print(f"Output: {output_file.name}")
        print(f"{'='*80}\n")

        # Collect all blocks from this file
        blocks = list(iterate_conversation_blocks(mhtml_file))

        if not blocks:
            print(f"  No conversation blocks found in {mhtml_file.name}")
            continue

        # Pair user questions with assistant answers
        current_question = None
        file_qa_pairs = 0
        qa_pairs = []

        for idx, speaker, text, _ in blocks:
            # Print to console
            print(f"Block {idx} [{speaker.upper()}]:")
            print("-" * 80)
            print(text)
            print()
            print("=" * 80)
            print()

            # Build Q&A pairs
            if speaker == 'user':
                current_question = text
            elif speaker == 'assistant' and current_question is not None:
                qa_pairs.append({
                    'question': current_question,
                    'answer': text
                })
                file_qa_pairs += 1
                total_qa_pairs += 1
                current_question = None

        # Write Q&A pairs to file
        with open(output_file, 'w', encoding='utf-8') as f:
            for qa_pair in qa_pairs:
                f.write(json.dumps(qa_pair, ensure_ascii=False) + '\n')
        print(f"  Extracted {file_qa_pairs} Q&A pairs to {output_file.name}\n")

    print(f"\n{'='*80}")
    print(f"Total: Written {total_qa_pairs} Q&A pairs across {len(mhtml_files)} files")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
