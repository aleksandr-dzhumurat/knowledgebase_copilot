#!/usr/bin/env python3
"""
Batch PDF to Markdown converter.

This script processes all PDF files in a given directory and converts them
to Markdown using the Ollama VLM (Granite3.3-vision) OCR pipeline.
"""

import argparse
import sys
from pathlib import Path
from typing import List

from ocr_graphite import convert_pdf_to_markdown


def find_pdf_files(input_dir: Path) -> List[Path]:
    """Find all PDF files in the input directory."""
    pdf_files = list(input_dir.glob("*.pdf"))
    return sorted(pdf_files)


def process_pdf_directory(
    input_dir: str,
    output_base: str = "./data",
    model: str = "ibm/granite3.3-vision:2b",
    recursive: bool = False
):
    """
    Process all PDF files in a directory.

    Args:
        input_dir: Path to directory containing PDF files
        output_base: Base directory for output (default: ./data)
        model: Ollama model to use (default: granite3.3-vision:2b)
        recursive: Process PDFs in subdirectories (default: False)
    """
    input_path = Path(input_dir).resolve()

    # Validate input directory
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    if not input_path.is_dir():
        raise ValueError(f"Input path is not a directory: {input_dir}")

    # Create output directory with same name as input directory
    output_base_path = Path(output_base)
    output_dir = output_base_path / input_path.name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find PDF files
    if recursive:
        pdf_files = sorted(input_path.rglob("*.pdf"))
    else:
        pdf_files = find_pdf_files(input_path)

    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return

    print(f"Found {len(pdf_files)} PDF file(s) in {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Using model: {model}")
    print("-" * 60)

    # Process each PDF
    success_count = 0
    failed_files = []

    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}] Processing: {pdf_file.name}")

        # Determine output path
        if recursive:
            # Preserve directory structure for recursive mode
            relative_path = pdf_file.relative_to(input_path)
            output_file = output_dir / relative_path.with_suffix('.md')
            output_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_file = output_dir / pdf_file.with_suffix('.md').name

        try:
            convert_pdf_to_markdown(
                input_path=str(pdf_file),
                output_path=str(output_file),
                model=model
            )
            success_count += 1
        except Exception as e:
            print(f"ERROR: Failed to process {pdf_file.name}: {e}")
            failed_files.append(pdf_file.name)
            continue

    # Summary
    print("\n" + "=" * 60)
    print(f"Processing complete!")
    print(f"Successfully converted: {success_count}/{len(pdf_files)} files")

    if failed_files:
        print(f"\nFailed files ({len(failed_files)}):")
        for filename in failed_files:
            print(f"  - {filename}")

    print(f"\nOutput directory: {output_dir}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Batch convert PDF files to Markdown using Ollama VLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all PDFs in a directory
  %(prog)s ~/Downloads/2025_10_papers

  # Specify custom output base directory
  %(prog)s ~/Downloads/papers --output ./output

  # Use a different model
  %(prog)s ~/Downloads/papers -m granite3.3-vision:8b

  # Process PDFs recursively in subdirectories
  %(prog)s ~/Documents/research -r
        """
    )

    parser.add_argument(
        "input_dir",
        help="Path to directory containing PDF files"
    )
    parser.add_argument(
        "-o", "--output",
        default="./data",
        help="Base output directory (default: ./data)"
    )
    parser.add_argument(
        "-m", "--model",
        default="ibm/granite3.3-vision:2b",
        help="Ollama model to use (default: ibm/granite3.3-vision:2b)"
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Process PDFs in subdirectories recursively"
    )

    args = parser.parse_args()

    try:
        process_pdf_directory(
            input_dir=args.input_dir,
            output_base=args.output,
            model=args.model,
            recursive=args.recursive
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
