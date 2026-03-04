
.PHONY: install web test

install:
	uv venv .venv --allow-existing
	. .venv/bin/activate && uv pip install -e .

web:
	. .venv/bin/activate && cd .. && adk web .

test:
	. .venv/bin/activate && pytest
