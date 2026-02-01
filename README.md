# Home Brain

## Dependencies

### System Dependencies

**pdflatex** (optional, for compiling .tex to PDF):
```bash
# macOS
brew install --cask mactex-no-gui
# or full version
brew install --cask mactex

# Ubuntu/Debian
sudo apt-get install texlive-latex-base texlive-latex-extra

# Check installation
pdflatex --version
```

### Python Dependencies

Install with:
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

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

## Tools

### Markdown Conversion

Convert markdown files to PDF or LaTeX:
```bash
# Convert to PDF
python src/convert_md_to_pdf.py docs/README.md

# Convert to LaTeX
python src/convert_md_to_pdf.py --format tex docs/README.md
```

### Markdown Validation

Check markdown heading hierarchy before conversion:
```bash
python src/check_md_hierarchy.py docs/README.md
```

See `docs/md_checking_rules.md` for validation rules and conversion features.

### Audio Processing

Requires `ffmpeg` (`brew install ffmpeg` on macOS).

**1. Extract audio from video:**
```bash
./scripts/extract_audio.sh ~/Downloads/recording.mp4
```
Output: `data/recording.mp3`

**2. Detect silence intervals:**
```bash
./scripts/silence_detector.sh recording.mp3
```
Output: `data/recording_silence.log`

**3. Split audio into 300-500s chunks at silence points:**
```bash
python3 scripts/audio_splitter.py data/recording.mp3
```
Output:
- `data/recording_silence.split.log` - split points log
- `data/recording_chunk_01.mp3` - audio chunks
- `data/recording_chunk_02.mp3`
- ...

**4. Transcribe audio to text:**
```bash
python3 scripts/audio_summarizer.py --prefix recording_chunk --limit 10
```
Output: `data/recognized_speech/recording_chunk_01.txt`, ...

Requires `GOOGLE_API_KEY` env var.

**5. Merge transcribed text files:**
```bash
python3 scripts/text_merger.py --prefix recording_chunk
```
Output: `data/recognized_speech/recording_chunk_merged.txt`