"""
uv run python scripts/retrieval.py \
  --md "data/Small Language Models for Efficient Agentic Tool Calling, Outperforming Large Models with Targeted Fine-tuning.md" \
  --query "LORA"
"""

import itertools
import os
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from extract_audio import extract_audio_pipeline
from langfuse import get_client
from pdf_to_md import convert, reformat_image_links
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.nebius import NebiusProvider
from whisper_to_srt import transcribe

Agent.instrument_all()
langfuse = get_client()


@dataclass
class SupportDependencies:
    home_dir: Path

model = OpenAIChatModel(
    'Qwen/Qwen3-32B-fast',
    provider=NebiusProvider(api_key=os.getenv('NEBIUS_API_KEY'))
)

project_manager_agent = Agent(
    model,
    instructions=(
        'You are a project manager agent assisting a software development team.'
        'Your task is to analyze team performance and provide actionable insights.'
        'You can process documents using the following tools:'
        'When the user mentions a file, call file_search to find it. If found, confirm the full path with the user before calling any tool. Be precise: just print the full path and ask to confirm, not be wordy.'
        'For .mp4 files: after confirmation call extract_audio, then automatically call extract_srt with the returned mp3 path.'
        'For .pdf files: after confirmation call pdf_to_md.'
    ),
    deps_type=SupportDependencies
)

@project_manager_agent.system_prompt
def add_home_dir(ctx: RunContext[SupportDependencies]) -> str:
    return f"The user's home directory is: {ctx.deps.home_dir}. Use it to resolve file paths like Downloads, Documents, etc."

SEARCH_DIRS = ["Downloads", "Documents", "PycharmProjects"]


@project_manager_agent.tool
def file_search(ctx: RunContext[SupportDependencies], filename: str) -> str:
    """Search for a file by name across Downloads, Documents and PycharmProjects under home_dir."""
    matches = []
    for search_dir in SEARCH_DIRS:
        base = ctx.deps.home_dir / search_dir
        if base.is_dir():
            matches.extend(base.rglob(filename))
    if not matches:
        return f"File '{filename}' not found in {SEARCH_DIRS}"
    if len(matches) == 1:
        return str(matches[0])
    return "Multiple files found:\n" + "\n".join(str(p) for p in matches)


@project_manager_agent.tool
async def extract_audio(_ctx: RunContext[SupportDependencies], video_path: str) -> str:
    """Extracts audio from a video file and saves it as an MP3 file. Expects a full resolved path."""
    output_file = extract_audio_pipeline(video_path)
    return f"Audio extracted to: {output_file}"


@project_manager_agent.tool
async def extract_srt(_ctx: RunContext[SupportDependencies], mp3_path: str) -> str:
    """Transcribes an MP3 file to an SRT subtitles file using Whisper."""
    srt_path = transcribe(mp3_path)
    return f"SRT saved to: {srt_path}"


@project_manager_agent.tool
def pdf_to_md(_ctx: RunContext[SupportDependencies], pdf_path: str) -> str:
    """Convert a PDF file to markdown. Skips if output already exists."""
    path = Path(pdf_path).resolve()
    output_dir = path.with_suffix("")
    md_path = output_dir.parent / f"{path.stem}.md"
    if md_path.exists():
        return f"Markdown already exists: {md_path}"
    convert(path, start_page=1)
    reformat_image_links(output_dir)
    return f"Markdown saved to: {md_path}"

def _spinner(stop_event: threading.Event) -> None:
    for frame in itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]):
        if stop_event.is_set():
            break
        sys.stdout.write(f"\r🤖 Thinking... {frame} ")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 20 + "\r")
    sys.stdout.flush()


if __name__ == "__main__":
    deps = SupportDependencies(home_dir=Path.home())
    print("🤖 Project Manager Agent ready. Type 'exit' to quit.\n")
    message_history = []
    while True:
        user_input = input("👨 You: ").strip()
        if user_input.lower() == "exit":
            print("🤖 Goodbye!")
            break
        stop = threading.Event()
        spinner = threading.Thread(target=_spinner, args=(stop,), daemon=True)
        spinner.start()
        result = project_manager_agent.run_sync(user_input, deps=deps, message_history=message_history)
        stop.set()
        spinner.join()
        message_history = result.all_messages()
        print(f"🤖 Agent: {result.output}\n")