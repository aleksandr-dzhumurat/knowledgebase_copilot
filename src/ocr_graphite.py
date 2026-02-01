"""
python3 src/ocr_graphite.py docs/ITOps_daily_standup.pdf -o data/output.md
"""

import argparse
import sys
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import ApiVlmOptions, VlmPipelineOptions
from docling.datamodel.pipeline_options_vlm_model import ResponseFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline


def ollama_vlm_options(model: str, prompt: str):
    """Configure Ollama VLM options for document processing."""
    options = ApiVlmOptions(
        url="http://localhost:11434/v1/chat/completions",
        params=dict(model=model),
        prompt=prompt,
        timeout=300,
        scale=1.0,
        response_format=ResponseFormat.MARKDOWN,
    )
    return options


def convert_pdf_to_markdown(
    input_path: str, output_path: str = None, model: str = "ibm/granite3.3-vision:2b"
):
    """
    Convert a PDF file to Markdown using Ollama VLM.

    Args:
        input_path: Path to the input PDF file
        output_path: Path to save the markdown file (optional, defaults to input name with .md extension)
        model: Ollama model to use for OCR (default: granite3.3-vision:2b)
    """
    input_file = Path(input_path)

    # Validate input file
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not input_file.suffix.lower() == ".pdf":
        raise ValueError(f"Input file must be a PDF, got: {input_file.suffix}")

    # Determine output path
    if output_path is None:
        output_path = input_file.with_suffix(".md")
    else:
        output_path = Path(output_path)

    print(f"Converting PDF: {input_path}")
    print(f"Using model: {model}")

    # Configure pipeline
    pipeline_options = VlmPipelineOptions(enable_remote_services=True)
    pipeline_options.vlm_options = ollama_vlm_options(
        model=model, prompt="OCR the full page to markdown."
    )

    # Create document converter
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                pipeline_cls=VlmPipeline,
            )
        }
    )

    # Convert PDF
    print("Processing PDF...")
    result = doc_converter.convert(str(input_file))
    markdown_content = result.document.export_to_markdown()

    # Save output
    output_path.write_text(markdown_content, encoding="utf-8")
    print(f"Markdown saved to: {output_path}")

    return markdown_content


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Convert PDF files to Markdown using Ollama VLM (Granite3.3-vision)"
    )
    parser.add_argument("input_pdf", help="Path to the input PDF file")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to the output Markdown file (default: same name as input with .md extension)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="ibm/granite3.3-vision:2b",
        help="Ollama model to use (default: ibm/granite3.3-vision:2b)",
    )

    args = parser.parse_args()

    try:
        convert_pdf_to_markdown(
            input_path=args.input_pdf, output_path=args.output, model=args.model
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
