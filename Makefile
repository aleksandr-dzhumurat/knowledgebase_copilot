CURRENT_DIR = $(shell pwd)

prepare-dirs:
	mkdir -p data/chroma_data || true

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