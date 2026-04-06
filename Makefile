CURRENT_DIR = $(shell pwd)
include .env
export

prepare-dirs:
	mkdir -p data/chroma_data
	mkdir -p data/history

run-chroma:
	docker run -d \
  	--name chromadb \
  	-p 8000:8000 \
  	-v ./data/chroma_data:/chroma/chroma \
  	chromadb/chroma:latest

latex:
	/Library/TeX/texbin/pdflatex -interaction=nonstopmode ${CURRENT_DIR}/data/llm-workflow-workshop.tex || true
	@echo "============================================================"
	@echo "PDF created: interview_questions.pdf"
	@ls -lh interview_questions.pdf 2>/dev/null || echo "PDF not found in current directory"
	@echo "============================================================"
# 	rm ${CURRENT_DIR}/*.log ${CURRENT_DIR}/*.aux ${CURRENT_DIR}/*.out 2>/dev/null || true

make chat:
	DATA_DIR=${CURRENT_DIR}/history PYTHONPATH=${CURRENT_DIR} uv run python scripts/chat.py