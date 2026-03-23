"""
Transcribe audio to .srt subtitles using Whisper on Apple Silicon.

Install:
    pip install mlx-whisper tqdm

Usage:
    uv run python scripts/whisper_to_srt.py audio.mp3
"""

import sys

import mlx_whisper as whisper
from tqdm import tqdm

MODEL = "mlx-community/whisper-medium"


def transcribe(audio_path: str, language: str = "en"):
    print(f"Transcribing: {audio_path}")
    print("Loading model and processing audio (this may take a moment)...")

    result = whisper.transcribe(audio_path, path_or_hf_repo=MODEL, language=language)
    segments = result["segments"]

    srt_path = audio_path.rsplit(".", 1)[0] + ".srt"
    with open(srt_path, "w") as f:
        for i, seg in tqdm(
            enumerate(segments, start=1), total=len(segments), desc="Writing .srt"
        ):
            f.write(f"{i}\n")
            f.write(f"{fmt(seg['start'])} --> {fmt(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")

    print(f"Saved: {srt_path}")


def fmt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python whisper_to_srt.py <audio.mp3>")
        sys.exit(1)
        
    audio_file = sys.argv[1]
    if audio_file.lower().endswith(".mp4"):
        print(f"Error: {audio_file} is an .mp4 video file.")
        print(f"Please extract the audio first by running: python scripts/extract_audio.py '{audio_file}'")
        expected_mp3 = audio_file.rsplit(".", 1)[0] + ".mp3"
        print(f"After doing that, run: uv run python scripts/whisper_to_srt.py '{expected_mp3}'")
        sys.exit(1)
        
    transcribe(audio_file)
