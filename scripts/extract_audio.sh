#!/bin/bash

set -e

export PATH="/opt/homebrew/bin:$PATH"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <path_to_video_file>"
    exit 1
fi

INPUT_FILE="$1"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File '$INPUT_FILE' not found"
    exit 1
fi

OUTPUT_DIR="$(dirname "$INPUT_FILE")"

BASENAME=$(basename "$INPUT_FILE")
OUTPUT_NAME="${BASENAME%.*}.mp3"
OUTPUT_FILE="$OUTPUT_DIR/$OUTPUT_NAME"

echo "Extracting audio from: $INPUT_FILE"
echo "Output file: $OUTPUT_FILE"

ffmpeg -i "$INPUT_FILE" -vn -acodec libmp3lame -q:a 2 "$OUTPUT_FILE"

echo "Done! Audio saved to: $OUTPUT_FILE"
