#!/usr/bin/env python3

import sys
import re
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/silence_detector.py <mp3_filename>")
        print("Example: python scripts/silence_detector.py recording.mp3")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    if not input_file.is_file():
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)

    output_file = input_file.parent / (input_file.stem + "_silence.log")

    print(f"Detecting silence in: {input_file}")
    print(f"Output log: {output_file}")

    result = subprocess.run(
        ["ffmpeg", "-i", str(input_file), "-af", "silencedetect=noise=-30dB:d=2", "-f", "null", "-"],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        text=True,
    )

    silence_lines = [
        line for line in result.stdout.splitlines()
        if re.search(r"silence_start|silence_end|silence_duration", line)
    ]

    output_file.write_text("\n".join(silence_lines) + "\n")

    print(f"Done! Silence intervals saved to: {output_file}")


if __name__ == "__main__":
    main()
