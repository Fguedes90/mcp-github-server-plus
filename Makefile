# Makefile for GitHub MCP Server

.PHONY: clean build docker-build docker-run

PORT ?= 3000

clean:
	rm -rf dist

build: clean
	npm run build

# Build the Docker image with the tag 'github-mcp-server'
docker-build: clean
	docker build -t github-mcp-server .

# Run the Docker container with stdio for MCP communication
docker-run:
	docker run -i --rm github-mcp-server

docker-debug-run:
	docker run --rm -it -p $(PORT):$(PORT) -e PORT=$(PORT) --entrypoint /bin/sh github-mcp-server 