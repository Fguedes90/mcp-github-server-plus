.PHONY: install dev-install format lint test coverage clean inspect run dev-server install-server

# Python configuration
PYTHON := python
UV := uv
SERVER_MODULE := mcp_pygithub
SERVER_SCRIPT := src/$(SERVER_MODULE)/__main__.py

# Virtual environment
VENV := .venv

# Install production dependencies
install:
	$(UV) venv
	. $(VENV)/bin/activate && $(UV) pip install -e .
	. $(VENV)/bin/activate && $(UV) pip install 'fastmcp>=0.1.0'

# Install development dependencies
dev-install: install
	. $(VENV)/bin/activate && $(UV) pip install -e ".[dev]"

# Format code using black and ruff
format:
	. $(VENV)/bin/activate && $(UV) run black src tests
	. $(VENV)/bin/activate && $(UV) run ruff --fix src tests

# Run linting checks
lint:
	. $(VENV)/bin/activate && $(UV) run mypy src tests
	. $(VENV)/bin/activate && $(UV) run ruff src tests
	. $(VENV)/bin/activate && $(UV) run black --check src tests

# Run tests
test:
	. $(VENV)/bin/activate && $(UV) run pytest

# Run tests with coverage report
coverage:
	. $(VENV)/bin/activate && $(UV) run pytest --cov=src --cov-report=html

# Run the server directly (legacy mode)
run:
	. $(VENV)/bin/activate && $(UV) run $(SERVER_SCRIPT)

# Run FastMCP development server with inspector
dev-server:
	. $(VENV)/bin/activate && $(UV) pip install --upgrade fastmcp
	. $(VENV)/bin/activate && fastmcp dev $(SERVER_SCRIPT)

# Install server in Claude Desktop
install-server:
	. $(VENV)/bin/activate && $(UV) pip install --upgrade fastmcp
	. $(VENV)/bin/activate && fastmcp install $(SERVER_SCRIPT) -e GITHUB_PERSONAL_ACCESS_TOKEN=$(GITHUB_PERSONAL_ACCESS_TOKEN)

# Run MCP Inspector on the server (legacy mode)
inspect:
	npx @modelcontextprotocol/inspector \
		--port=3001 \
		-- \
		./run-server.sh $(GITHUB_PERSONAL_ACCESS_TOKEN)

# Clean up generated files and virtual environment
clean:
	rm -rf $(VENV)
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.pyc" -exec rm -rf {} +

# Show help
help:
	@echo "Available commands:"
	@echo "  make install         - Install production dependencies"
	@echo "  make dev-install    - Install development dependencies"
	@echo "  make format         - Format code using black and ruff"
	@echo "  make lint           - Run all linting checks"
	@echo "  make test           - Run tests"
	@echo "  make coverage       - Run tests with coverage report"
	@echo "  make run            - Run the server directly (legacy mode)"
	@echo "  make dev-server     - Run FastMCP development server with inspector"
	@echo "  make install-server - Install server in Claude Desktop"
	@echo "  make inspect        - Run MCP Inspector on the server (legacy mode)"
	@echo "  make clean          - Clean up generated files"