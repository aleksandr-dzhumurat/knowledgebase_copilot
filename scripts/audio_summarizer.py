import argparse
import logging
import os
from pathlib import Path
from typing import Iterator, Optional

from dotenv import load_dotenv
from google import genai

load_dotenv()

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)


class GeminiAdapter:
    """Adapter for Google Gemini API."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        self._model = model
        self._client = genai.Client(
            api_key=os.environ.get("GOOGLE_API_KEY"),
            vertexai=False,
        )


def audio_file_iterator(
    limit: Optional[int] = None,
    prefix: Optional[str] = None,
) -> Iterator[Path]:
    """Iterate over .mp3 files from data directory.

    Args:
        limit: Maximum number of files to yield. None for unlimited.
        prefix: Filter files that contain this prefix in the filename. None for all files.

    Yields:
        Path objects for each .mp3 file.
    """
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data" / "audio"

    count = 0
    for mp3_file in sorted(data_dir.glob("*.mp3")):
        if prefix is not None and prefix not in mp3_file.name:
            continue
        if limit is not None and count >= limit:
            break
        yield mp3_file
        count += 1


llm_adapter = GeminiAdapter()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize audio files using Gemini")
    parser.add_argument(
        "--prefix", help="Filter files containing this prefix in filename"
    )
    parser.add_argument(
        "--limit", type=int, default=1, help="Max files to process (default: 1)"
    )
    args = parser.parse_args()

    # Create output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "data" / "recognized_speech"
    output_dir.mkdir(parents=True, exist_ok=True)

    for f in audio_file_iterator(limit=args.limit, prefix=args.prefix):
        print(f"Processing: {f}")

        audio_file = llm_adapter._client.files.upload(
            file=f,
            config={"mime_type": "audio/mpeg"},
        )
        print(f"Uploaded: {audio_file.name}")
        audio_part = audio_file

        response = llm_adapter._client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                "Please provide a concise summary of this audio recording. "
                "Highlight the main topics discussed and any significant conclusions.",
                audio_part,
            ],
        )

        # Save response to file
        output_file = output_dir / f"{f.stem}.txt"
        output_file.write_text(response.text, encoding="utf-8")
        print(f"Saved: {output_file}")
