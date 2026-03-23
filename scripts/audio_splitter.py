#!/usr/bin/env python3
"""
Audio Splitter - Splits audio files into 300-500 second intervals at silence points.

Uses a greedy algorithm to find optimal split points at silence intervals.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SilencePeriod:
    start: float
    end: float
    duration: float

    @property
    def center(self) -> float:
        return (self.start + self.end) / 2


@dataclass
class Interval:
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


def parse_silence_log(log_path: Path) -> list[SilencePeriod]:
    """Parse silence detection log file and return list of silence periods."""
    silence_periods = []
    current_start = None

    with open(log_path, 'r') as f:
        for line in f:
            start_match = re.search(r'silence_start:\s*([\d.]+)', line)
            if start_match:
                current_start = float(start_match.group(1))
                continue

            end_match = re.search(r'silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)', line)
            if end_match and current_start is not None:
                end = float(end_match.group(1))
                duration = float(end_match.group(2))
                silence_periods.append(SilencePeriod(current_start, end, duration))
                current_start = None

    return silence_periods


def find_split_points(silence_periods: list[SilencePeriod],
                      total_duration: float,
                      min_interval: float = 300,
                      max_interval: float = 500) -> list[Interval]:
    """
    Greedy algorithm to find optimal split points.

    For each interval:
    1. Accumulate time until reaching min_interval (300s)
    2. Find all silence periods between min_interval and max_interval from interval start
    3. Select the silence period with maximum duration
    4. Use center of that silence as the split point
    """
    intervals = []
    current_start = 0.0

    while current_start < total_duration:
        min_boundary = current_start + min_interval
        max_boundary = current_start + max_interval

        # If remaining audio is less than max_interval, take it all
        if total_duration - current_start <= max_interval:
            intervals.append(Interval(current_start, total_duration))
            break

        # Find silence periods within valid range [min_boundary, max_boundary]
        candidates = [
            sp for sp in silence_periods
            if sp.start >= min_boundary and sp.end <= max_boundary
        ]

        if candidates:
            # Select silence period with maximum duration
            best_silence = max(candidates, key=lambda sp: sp.duration)
            split_point = best_silence.center
            intervals.append(Interval(current_start, split_point))
            current_start = split_point
        else:
            # No silence in range - try to find closest silence after min_boundary
            fallback = [sp for sp in silence_periods if sp.start >= min_boundary]
            if fallback:
                # Take the first silence after min_boundary
                best_silence = fallback[0]
                split_point = best_silence.center
                intervals.append(Interval(current_start, split_point))
                current_start = split_point
            else:
                # No more silence periods - take remaining audio
                intervals.append(Interval(current_start, total_duration))
                break

    return intervals


def format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(audio_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    return float(result.stdout.strip())


def split_audio_file(audio_path: Path, intervals: list[Interval]) -> list[Path]:
    """Split audio file into chunks based on intervals using ffmpeg."""
    output_dir = audio_path.parent / audio_path.stem
    output_dir.mkdir(exist_ok=True)
    base_name = audio_path.stem
    output_files = []

    for i, interval in enumerate(intervals, 1):
        output_path = output_dir / f"{base_name}_chunk_{i:02d}.mp3"
        duration = interval.end - interval.start

        cmd = [
            'ffmpeg', '-y', '-i', str(audio_path),
            '-ss', str(interval.start),
            '-t', str(duration),
            '-acodec', 'copy',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed for chunk {i}: {result.stderr}")

        output_files.append(output_path)
        print(f"Created: {output_path.name}")

    return output_files


def main():
    parser = argparse.ArgumentParser(description='Split audio into intervals at silence points')
    parser.add_argument('audio_file', help='Path to audio file (.mp3)')
    parser.add_argument('--min-interval', type=float, default=300, help='Minimum interval duration (default: 300)')
    parser.add_argument('--max-interval', type=float, default=500, help='Maximum interval duration (default: 500)')
    args = parser.parse_args()

    audio_path = Path(args.audio_file)
    if not audio_path.exists():
        print(f"Error: Audio file '{audio_path}' not found", file=sys.stderr)
        sys.exit(1)

    # Derive silence log path from audio file
    log_path = audio_path.with_name(audio_path.stem + '_silence.log')
    if not log_path.exists():
        print(f"Error: Silence log '{log_path}' not found. Run silence_detector.py first.", file=sys.stderr)
        sys.exit(1)

    silence_periods = parse_silence_log(log_path)
    if not silence_periods:
        print("Error: No silence periods found in log file", file=sys.stderr)
        sys.exit(1)

    # Get duration from audio file
    total_duration = get_audio_duration(audio_path)
    print(f"Audio duration: {format_time(total_duration)}")

    intervals = find_split_points(
        silence_periods,
        total_duration,
        args.min_interval,
        args.max_interval
    )

    # Output results
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

    # Split audio file into chunks
    print(f"\nSplitting audio into {len(intervals)} chunks...")
    output_files = split_audio_file(audio_path, intervals)
    print(f"\nDone! Created {len(output_files)} audio chunks in {audio_path.parent}")


if __name__ == '__main__':
    main()
