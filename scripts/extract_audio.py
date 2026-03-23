#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/extract_audio.py <path_to_video_file>")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    if not input_file.is_file():
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)

    output_file = input_file.with_suffix(".mp3")

    print(f"Extracting audio from: {input_file}")
    print(f"Output file: {output_file}")

    subprocess.run(
        ["ffmpeg", "-i", str(input_file), "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(output_file)],
        check=True,
    )

    print(f"Done! Audio saved to: {output_file}")


if __name__ == "__main__":
    main()
