# Home Brain

## Dependencies

### Python Dependencies

Install with:
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Tools

### Markdown Validation

Check markdown heading hierarchy:
```bash
python src/check_md_hierarchy.py docs/README.md
```

See `docs/md_checking_rules.md` for validation rules.

### Audio Processing

Requires `ffmpeg` (`brew install ffmpeg` on macOS).

**1. Extract audio from video:**
```bash
python scripts/extract_audio.py ~/Downloads/recording.mp4
```
Output: `~/Downloads/recording.mp3`

**2. Detect silence intervals:**
```bash
python scripts/silence_detector.py ~/Downloads/recording.mp3
```
Output: `~/Downloads/recording_silence.log`

**3. Split audio into 300-500s chunks at silence points:**
```bash
python scripts/audio_splitter.py ~/Downloads/recording.mp3
```
Output:
- `~/Downloads/recording_silence.split.log` - split points log
- `~/Downloads/recording/recording_chunk_01.mp3` - audio chunks
- `~/Downloads/recording/recording_chunk_02.mp3`
- ...

**4. Transcribe audio to text:**

Option A — Whisper (Apple Silicon, no API key required):
```bash
uv run python scripts/whisper_to_srt.py ~/Downloads/recording_chunk_01.mp3
```
Output: `~/Downloads/recording_chunk_01.srt`

Requires `mlx-whisper` and `tqdm`: `uv pip install mlx-whisper tqdm`

Option B — Google API:
```bash
python scripts/audio_summarizer.py --prefix recording_chunk --limit 10
```
Output: `data/recognized_speech/recording_chunk_01.txt`, ...

Requires `GOOGLE_API_KEY` env var.

**5. Merge transcribed text files:**
```bash
python scripts/text_merger.py --prefix recording_chunk
```
Output: `data/recognized_speech/recording_chunk_merged.txt`



## Services

### Chroma
Version endpoint: http://0.0.0.0:8000/api/v2/version

### Ollama Models
```bash
ollama pull granite3.3:8b
ollama pull nomic-embed-text
```

### Ollama Embeddings Generation
```bash
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "Hello, this is a test"
}'
```
