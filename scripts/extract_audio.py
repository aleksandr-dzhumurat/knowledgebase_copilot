#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


def extract_audio_pipeline(video_path: str = None):
    if video_path is None:
        if len(sys.argv) < 2:
            print("Usage: python scripts/extract_audio.py <path_to_video_file>")
            sys.exit(1)
        video_path = sys.argv[1]

    input_file = Path(video_path)

    if not input_file.is_file():
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)

    output_file = input_file.with_suffix(".mp3")

    if output_file.is_file():
        print(f"Audio already exists: {output_file}")
        return output_file

    print(f"Extracting audio from: {input_file}")
    print(f"Output file: {output_file}")

    subprocess.run(
        ["ffmpeg", "-i", str(input_file), "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(output_file)],
        check=True,
    )

    print(f"Done! Audio saved to: {output_file}")
    return output_file


if __name__ == "__main__":
    extract_audio_pipeline()
