import logging
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from langfuse import get_client
from pydantic_ai import Agent, RunContext
from pydantic_ai.agent import InstrumentationSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.nebius import NebiusProvider

from prompts import (
    PROJECT_MANAGER_INSTRUCTIONS,
    RETRIEVAL_AGENT_INSTRUCTIONS,
    SUMMARIZE_INSTRUCTIONS,
    home_dir_prompt,
)
from mindbase_layer.audio import convert_to_mp3, extract_audio_pipeline, transcribe
from mindbase_layer.pdf_to_md import convert, reformat_image_links
from mindbase_layer.retrieve_md import DocumentIndex, DocumentNode, summarize_srt
from mindbase_layer.youtube import download_audio as yt_download_audio
from mindbase_layer.youtube import download_video as yt_download_video

Agent.instrument_all(InstrumentationSettings(include_content=True, version=1))
langfuse = get_client()
logger = logging.getLogger(__name__)


@dataclass
class SupportDependencies:
    home_dir: Path


@dataclass
class RetrievalDependencies:
    md_path: Path


@dataclass
class SummarizeDependencies:
    text: str
    language: str


_main_model = OpenAIChatModel(
    'Qwen/Qwen3-32B',
    provider=NebiusProvider(api_key=os.getenv('NEBIUS_API_KEY'))
)

_retrieval_model = OpenAIChatModel(
    'Qwen/Qwen3-30B-A3B-Instruct-2507',
    provider=NebiusProvider(api_key=os.getenv('NEBIUS_API_KEY'))
)

retrieval_agent = Agent(
    _retrieval_model,
    instructions=RETRIEVAL_AGENT_INSTRUCTIONS,
    deps_type=RetrievalDependencies,
    output_type=str,
)

_summarize_agent = Agent(
    _main_model,
    instructions=SUMMARIZE_INSTRUCTIONS,
    deps_type=SummarizeDependencies,
    output_type=str,
)


@_summarize_agent.system_prompt
def summarize_system_prompt(ctx: RunContext[SummarizeDependencies]) -> str:
    return (
        f"Respond in: {ctx.deps.language}\n\n"
        f"Transcript:\n{ctx.deps.text}"
    )


@retrieval_agent.tool
def query_documents(ctx: RunContext[RetrievalDependencies], query: str) -> str:
    """Search the indexed markdown document(s) using TF-IDF cosine similarity."""
    md_path = ctx.deps.md_path
    if md_path.is_dir():
        index = DocumentIndex.from_dir(md_path)
    elif md_path.suffix == '.srt':
        index = DocumentIndex.from_srt_file(md_path)
    else:
        index = DocumentIndex.from_md_file(md_path)
    results = index.search(query, top_k=5)
    if not results:
        return f"No results found for query: '{query}'"
    lines = [f"Found {len(results)} matching nodes:"]
    for score, node in results:
        lines.append(f"\n[{score:.4f}] {node.header}")
        if node.body:
            lines.append(node.body[:500])
    return "\n".join(lines)


project_manager_agent = Agent(
    _main_model,
    instructions=PROJECT_MANAGER_INSTRUCTIONS,
    deps_type=SupportDependencies
)


@project_manager_agent.system_prompt
def add_home_dir(ctx: RunContext[SupportDependencies]) -> str:
    return home_dir_prompt(ctx.deps.home_dir)


SEARCH_DIRS = ["Downloads", "Documents", "PycharmProjects"]


@project_manager_agent.tool
def file_search(ctx: RunContext[SupportDependencies], filename: str) -> str:
    """Search for a file by name across Downloads, Documents and PycharmProjects under home_dir.
    If filename is an absolute path, checks existence directly without searching."""
    path = Path(filename)
    if path.is_absolute():
        return str(path) if path.exists() else f"File not found: {path}"
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
def file_fuzzy_search(ctx: RunContext[SupportDependencies], query: str) -> str:
    """Fuzzy search for a file by query across Downloads, Documents and PycharmProjects.
    Indexes all filenames with TF-IDF and returns top-10 matches. Use as fallback when file_search returns nothing."""
    nodes = []
    for search_dir in SEARCH_DIRS:
        base = ctx.deps.home_dir / search_dir
        if base.is_dir():
            for path in base.rglob("*"):
                if path.is_file():
                    normalized = path.stem.replace("_", " ").replace("-", " ")
                    nodes.append(DocumentNode(header=path.name, body=normalized, source=path))
    if not nodes:
        return "No files found in search directories."
    index = DocumentIndex(nodes)
    results = index.search(query, top_k=10)
    if not results:
        return f"No files matching '{query}' found."
    lines = [f"Top {len(results)} fuzzy matches for '{query}':"]
    for score, node in results:
        lines.append(f"  [{score:.4f}] {node.source}")
    return "\n".join(lines)


@project_manager_agent.tool
async def summarize_video(ctx: RunContext[SupportDependencies], video_path: str, spoken_language: str = "en") -> str:
    """Summarize a video lecture. Generates subtitles first if they don't exist.
    spoken_language: language spoken in the video (BCP-47, e.g. 'en', 'ru'). Summary will be in the same language.
    """
    path = Path(video_path)
    srt_path = path.with_suffix(".srt")
    if not srt_path.exists():
        logger.info("summarize_video: generating subtitles for %s (lang=%s)", path.name, spoken_language)
        mp3_path = str(extract_audio_pipeline(video_path))
        srt_path = Path(transcribe(mp3_path, language=spoken_language))
    else:
        logger.info("summarize_video: using existing subtitles %s", srt_path.name)
    logger.info("summarize_video: indexing %s", srt_path.name)
    nodes = summarize_srt(srt_path)
    if not nodes:
        return f"Could not extract text from {srt_path}"
    logger.info("summarize_video: summarizing %d chunks", len(nodes))
    full_text = "\n\n".join(
        f"[{node.header}]\n{node.body}" for node in nodes
    )
    result = await _summarize_agent.run(
        "Summarize this video transcript.",
        deps=SummarizeDependencies(text=full_text, language=spoken_language),
        usage=ctx.usage,
    )
    u = result.usage()
    logger.info("summarize_video tokens: input=%d output=%d total=%d", u.input_tokens, u.output_tokens, u.input_tokens + u.output_tokens)
    summary_path = srt_path.with_name(f"{srt_path.stem}_summary.md")
    summary_path.write_text(result.output, encoding="utf-8")
    logger.info("summarize_video: summary saved to %s", summary_path)
    return result.output


@project_manager_agent.tool
async def generate_subtitles(_ctx: RunContext[SupportDependencies], video_path: str, language: str = "en") -> str:
    """Generate an SRT subtitles file from a video. language is a BCP-47 code e.g. 'en', 'ru'. Expects a full resolved path."""
    mp3_path = str(extract_audio_pipeline(video_path))
    srt_path = transcribe(mp3_path, language=language)
    return f"Subtitles saved to: {srt_path}"


@project_manager_agent.tool
def m4a_to_mp3(_ctx: RunContext[SupportDependencies], input_path: str) -> str:
    """Convert an m4a (or other audio) file to mp3. Expects a full resolved path."""
    output_file = convert_to_mp3(input_path)
    return f"MP3 saved to: {output_file}"


@project_manager_agent.tool
async def search_file_content(ctx: RunContext[SupportDependencies], md_path: str, query: str) -> str:
    """Search the content of a markdown file or directory using the retrieval agent."""
    path = Path(md_path).expanduser().resolve()
    result = await retrieval_agent.run(query, deps=RetrievalDependencies(md_path=path), usage=ctx.usage)
    return result.output


_YOUTUBE_DIR = Path(__file__).parent.parent / "data" / "youtube"


@project_manager_agent.tool
async def youtube_download(_ctx: RunContext[SupportDependencies], url: str, mode: str = "video") -> str:
    """Download a YouTube video or audio track. mode must be 'video' or 'audio'."""
    _YOUTUBE_DIR.mkdir(parents=True, exist_ok=True)
    if mode == "audio":
        path = yt_download_audio(url, output_dir=_YOUTUBE_DIR)
    else:
        path = yt_download_video(url, output_dir=_YOUTUBE_DIR)
    return f"Downloaded to: {path}"


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


@project_manager_agent.tool
def remove_file(_ctx: RunContext[SupportDependencies], file_path: str) -> str:
    """Delete a file or directory. Uses shutil.rmtree for directories, Path.unlink for files."""
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Not found: {path}"
    if path.is_dir():
        shutil.rmtree(path)
        return f"Directory removed: {path}"
    path.unlink()
    return f"File removed: {path}"
