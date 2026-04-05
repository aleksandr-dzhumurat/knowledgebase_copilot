import itertools
import os
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from extract_audio import extract_audio_pipeline
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.nebius import NebiusProvider


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
        'Before calling extract_audio, use file_exist to resolve the full path, then confirm it with the user. Be precise: just print the full path and ask to confirm, not be wordy.'
    ),
    deps_type=SupportDependencies
)

@project_manager_agent.system_prompt
def add_home_dir(ctx: RunContext[SupportDependencies]) -> str:
    return f"The user's home directory is: {ctx.deps.home_dir}. Use it to resolve file paths like Downloads, Documents, etc."

@project_manager_agent.tool
def file_exist(ctx: RunContext[SupportDependencies], video_path: str) -> str:
    """Resolves a file path relative to home_dir and checks if it exists. Returns the full resolved path."""
    path = Path(video_path).expanduser()
    if not path.exists():
        relative = Path(*path.parts[1:]) if path.is_absolute() else path
        resolved = ctx.deps.home_dir
        for part in relative.parts:
            matches = [p for p in resolved.iterdir() if p.name.lower() == part.lower()]
            resolved = matches[0] if matches else resolved / part
        path = resolved
    return str(path) if path.exists() else f"File not found: {path}"


@project_manager_agent.tool
async def extract_audio(_ctx: RunContext[SupportDependencies], video_path: str) -> str:
    """Extracts audio from a video file and saves it as an MP3 file. Expects a full resolved path."""
    output_file = extract_audio_pipeline(video_path)
    return f"Audio extracted to: {output_file}"

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