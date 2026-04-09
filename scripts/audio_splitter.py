#!/usr/bin/env python3
"""
Audio Splitter - Splits audio files into 300-500 second intervals at silence points.

Usage:
    uv run python scripts/audio_splitter.py <audio.mp3> [--min-interval 300] [--max-interval 500]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from utils.audio import (
    detect_silence, find_split_points, format_time, get_audio_duration,
    parse_silence_log, split_audio_file,
)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Split audio into intervals at silence points')
    parser.add_argument('audio_file', help='Path to audio file (.mp3)')
    parser.add_argument('--min-interval', type=float, default=300, help='Minimum interval duration (default: 300)')
    parser.add_argument('--max-interval', type=float, default=500, help='Maximum interval duration (default: 500)')
    args = parser.parse_args()

    audio_path = Path(args.audio_file)
    if not audio_path.exists():
        print(f"Error: Audio file '{audio_path}' not found", file=sys.stderr)
        sys.exit(1)

    log_path = audio_path.with_name(audio_path.stem + '_silence.log')
    if not log_path.exists():
        print("Silence log not found, running silence detection...")
        detect_silence(str(audio_path))

    silence_periods = parse_silence_log(log_path)
    if not silence_periods:
        print("Error: No silence periods found in log file", file=sys.stderr)
        sys.exit(1)

    total_duration = get_audio_duration(audio_path)
    print(f"Audio duration: {format_time(total_duration)}")

    intervals = find_split_points(silence_periods, total_duration, args.min_interval, args.max_interval)

    output_path = log_path.with_suffix('.split.log')
    with open(output_path, 'w') as f:
        f.write(f"# Audio split points (min={args.min_interval}s, max={args.max_interval}s)\n")
        f.write(f"# Total duration: {format_time(total_duration)}\n")
        f.write(f"# Number of intervals: {len(intervals)}\n\n")
        for i, interval in enumerate(intervals, 1):
            line = f"interval_{i:03d}: {format_time(interval.start)} -> {format_time(interval.end)} (duration: {interval.duration:.2f}s)"
            print(line)
            f.write(line + "\n")

    print(f"\nSplit points saved to: {output_path}")
    print(f"\nSplitting audio into {len(intervals)} chunks...")
    output_files = split_audio_file(audio_path, intervals)
    print(f"\nDone! Created {len(output_files)} audio chunks in {audio_path.parent}")
