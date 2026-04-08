import os
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from utils.audio import extract_audio_pipeline
from langfuse import get_client
from utils.pdf import convert, reformat_image_links
from pydantic_ai import Agent, RunContext
from pydantic_ai.agent import InstrumentationSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.nebius import NebiusProvider
from utils.retrieve import DocumentIndex, DocumentNode
from whisper_to_srt import transcribe

Agent.instrument_all(InstrumentationSettings(include_content=True, version=1))
langfuse = get_client()


@dataclass
class SupportDependencies:
    home_dir: Path


@dataclass
class RetrievalDependencies:
    md_path: Path


_main_model = OpenAIChatModel(
    'Qwen/Qwen3-32B-fast',
    provider=NebiusProvider(api_key=os.getenv('NEBIUS_API_KEY'))
)

_retrieval_model = OpenAIChatModel(
    'Qwen/Qwen3-30B-A3B-Instruct-2507',
    provider=NebiusProvider(api_key=os.getenv('NEBIUS_API_KEY'))
)

retrieval_agent = Agent(
    _retrieval_model,
    instructions=(
        'You are a document retrieval specialist. '
        'Use the search_documents tool to find relevant content in indexed markdown files. '
        'If the search returns no results, rephrase the query using synonyms or simpler terms and call search_documents again (at most 2 retries). '
        'Return the most relevant excerpts you found, or clearly state that nothing was found.'
    ),
    deps_type=RetrievalDependencies,
    output_type=str,
)


@retrieval_agent.tool
def search_documents(ctx: RunContext[RetrievalDependencies], query: str) -> str:
    """Search the indexed markdown document(s) using TF-IDF cosine similarity."""
    md_path = ctx.deps.md_path
    if md_path.is_dir():
        index = DocumentIndex.from_dir(md_path)
    else:
        index = DocumentIndex.from_md_file(md_path)
    results, total = index.search(query, top_k=5)
    if not results:
        return f"No results found for query: '{query}'"
    lines = [f"Found {len(results)} of {total} matching nodes:"]
    for score, node in results:
        lines.append(f"\n[{score:.4f}] {node.header}")
        if node.body:
            lines.append(node.body[:500])
    return "\n".join(lines)


project_manager_agent = Agent(
    _main_model,
    instructions=(
        'You are a project manager agent assisting a software development team.'
        'Your task is to analyze team performance and provide actionable insights.'
        'You can process documents using the following tools:'
        'When the user mentions a file, call file_search to find it. If file_search returns nothing, call file_fuzzy_search with the same query. If found, confirm the full path with the user before calling any tool. Be precise: just print the full path and ask to confirm, not be wordy.'
        'For .mp4 files: after confirmation call extract_audio, then automatically call extract_srt with the returned mp3 path.'
        'For .pdf files: after confirmation call pdf_to_md.'
        'When the user asks about the content of a markdown file or directory, call search_file_content with the resolved path and the user query.'
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
    results, _ = index.search(query, top_k=10)
    if not results:
        return f"No files matching '{query}' found."
    lines = [f"Top {len(results)} fuzzy matches for '{query}':"]
    for score, node in results:
        lines.append(f"  [{score:.4f}] {node.source}")
    return "\n".join(lines)


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
async def search_file_content(ctx: RunContext[SupportDependencies], md_path: str, query: str) -> str:
    """Search the content of a markdown file or directory using the retrieval agent."""
    path = Path(md_path).expanduser().resolve()
    result = await retrieval_agent.run(query, deps=RetrievalDependencies(md_path=path), usage=ctx.usage)
    return result.output


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
