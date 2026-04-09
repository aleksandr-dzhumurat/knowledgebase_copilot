"""
Extract a page range from a PDF and optionally clean image markers from a markdown file.

To install dependencies:
    uv pip install pypdf docling

Usage:
    uv run python scripts/pdf_to_md.py --start 148 --end 155 --input $(pwd)/data/long_boring_demo.pdf
    uv run python scripts/pdf_to_md.py --input $(pwd)/week_01_agents_shrinked.pdf
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from utils.pdf_to_md import convert, filter_pages, get_pdf_num_pages, reformat_image_links, remove_images

__all__ = ["convert", "filter_pages", "get_pdf_num_pages", "reformat_image_links", "remove_images"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract PDF pages and clean markdown images")
    parser.add_argument("--start", type=int, default=1, help="First page to extract (1-indexed)")
    parser.add_argument("--end", type=int, help="Last page to extract (1-indexed)")
    parser.add_argument("--input", type=Path, required=True, help="Path to source PDF file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    end_provided = args.end is not None
    if args.end is None:
        args.end = get_pdf_num_pages(args.input)

    if not end_provided and args.start == 1:
        extracted_pdf = args.input
    else:
        extracted_pdf = filter_pages(args.start, args.end, args.input)

    convert(extracted_pdf, args.start)

    output_dir = extracted_pdf.resolve().with_suffix("")
    reformat_image_links(output_dir)

    logging.info("Done! Processed %d pages.", args.end - args.start + 1)
