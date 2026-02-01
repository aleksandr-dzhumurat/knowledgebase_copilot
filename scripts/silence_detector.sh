#!/bin/bash

set -e

export PATH="/opt/homebrew/bin:$PATH"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <mp3_filename>"
    echo "Example: $0 recording.mp3"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_DIR/data/audio"

INPUT_FILE="$DATA_DIR/$1"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File '$INPUT_FILE' not found"
    exit 1
fi

BASENAME=$(basename "$INPUT_FILE")
OUTPUT_NAME="${BASENAME%.*}_silence.log"
OUTPUT_FILE="$DATA_DIR/$OUTPUT_NAME"

echo "Detecting silence in: $INPUT_FILE"
echo "Output log: $OUTPUT_FILE"

ffmpeg -i "$INPUT_FILE" -af silencedetect=noise=-30dB:d=2 -f null - 2>&1 | \
    grep -E "silence_start|silence_end|silence_duration" > "$OUTPUT_FILE"

echo "Done! Silence intervals saved to: $OUTPUT_FILE"
