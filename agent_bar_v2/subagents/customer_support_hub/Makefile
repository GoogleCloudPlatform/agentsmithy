ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: install
install: # Install virtual environment with uv
	@echo "🚀 Creating virtual environment using uv"
	@uv sync

.PHONY: web
web: # Run the ADK web demo server
	@uv run adk web --reload src/agents/

.PHONY: api_server
api_server: # Run the ADK FastAPI server
	@uv run adk api_server src/agents/
