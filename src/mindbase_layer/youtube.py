import logging
from pathlib import Path

from pytubefix import YouTube
from pytubefix.cli import on_progress


def download_video(url: str, output_dir: Path | None = None) -> Path:
    """Download a YouTube video at highest resolution. Returns the saved file path."""
    yt = YouTube(url, on_progress_callback=on_progress)
    stream = yt.streams.get_highest_resolution()
    if stream is None:
        raise ValueError(f"No video stream found for {url}")
    out_dir = str(output_dir) if output_dir else None
    out_path = stream.download(output_path=out_dir)
    logging.info("Video saved: %s", out_path)
    return Path(out_path)


def download_audio(url: str, output_dir: Path | None = None) -> Path:
    """Download a YouTube video as MP3 audio. Returns the saved file path."""
    yt = YouTube(url, on_progress_callback=on_progress)
    stream = yt.streams.get_audio_only()
    if stream is None:
        raise ValueError(f"No audio stream found for {url}")
    out_dir = str(output_dir) if output_dir else None
    out_path = stream.download(output_path=out_dir, mp3=True)
    logging.info("Audio saved: %s", out_path)
    return Path(out_path)
