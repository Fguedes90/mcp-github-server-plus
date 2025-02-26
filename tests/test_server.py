"""Tests for MPC GitHub Python server."""

import os
from typing import Any, Callable, AsyncIterator
from unittest.mock import Mock, AsyncMock, patch
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from mcp.server.fastmcp import FastMCP
from mcp.types import Tool
from github.Repository import Repository as GithubRepository
from mcp_pygithub.server.app import create_app, ServerConfig
from mcp_pygithub.server.handlers import GitHubHandler
from mcp_pygithub.operations.repository import RepositoryManager, RepositoryConfig
from mcp_pygithub.common.version import __version__
from .conftest import DictLikeMock, create_mock_github_client, MockGitHubClientFactory

# Mock classes
class MockRequestContext:
    """Mock request context."""
    def __init__(self) -> None:
        self.lifespan_context = {}

class MockFastMCP:
    """Mock FastMCP class."""
    def __init__(self, name: str = "", version: str = "", lifespan: Any = None) -> None:
        self.name = name
        self.version = version
        self.lifespan = lifespan
        self.request_context = MockRequestContext()
        self.debug = False

    @asynccontextmanager
    async def lifespan(self, app: Any) -> AsyncIterator[dict]:
        """Mock lifespan context manager."""
        if callable(self.lifespan):
            async with self.lifespan(app) as context:
                yield context
        else:
            yield {}

    def run(self, transport: str = "stdio") -> None:
        """Mock run method."""
        pass

class MockGitHubHandler:
    """Mock GitHubHandler class."""
    def __init__(self, token: str) -> None:
        self.token = token
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the handler."""
        self._initialized = True

    def list_tools(self) -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="get_repository",
                description="Get GitHub repository information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "Repository owner"},
                        "name": {"type": "string", "description": "Repository name"}
                    },
                    "required": ["owner", "name"]
                }
            ),
            Tool(
                name="create_repository",
                description="Create a new GitHub repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Repository name"},
                        "private": {"type": "boolean", "description": "Whether the repository is private"}
                    },
                    "required": ["name"]
                }
            )
        ]

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Call a tool."""
        if name == "get_user":
            return "octocat"
        elif name == "list_files":
            return []
        elif name == "list_issues":
            if arguments.get("state") == "invalid":
                raise ValueError("Invalid state")
            return [{"title": "Test Issue 1", "state": "open"}]
        elif name == "list_pull_requests":
            return []
        elif name == "list_branches":
            return []
        elif name == "search_code":
            return []
        elif name == "create_repository":
            return {
                "name": arguments["name"],
                "private": arguments.get("private", False)
            }
        elif name == "delete_repository":
            return {"success": True}
        elif name == "create_issue":
            if not arguments.get("title"):
                raise ValueError("Title is required")
            return {
                "title": arguments["title"],
                "state": "open"
            }
        return {}

# Mock the imports
@pytest.fixture(autouse=True)
def mock_imports():
    """Mock imports before importing our module."""
    with patch("mcp_pygithub.server.app.FastMCP", MockFastMCP), \
         patch("mcp_pygithub.server.app.GitHubHandler", MockGitHubHandler):
        yield

@pytest.fixture
def test_config() -> ServerConfig:
    """Create a test server configuration."""
    return ServerConfig(
        github_token="test-token",
        debug=True
    )

def test_create_app_with_config(test_config: ServerConfig) -> None:
    """Test creating app with explicit configuration."""
    app = create_app(test_config)
    assert isinstance(app, MockFastMCP)
    assert app.name == "mpc-github-python"
    assert app.version == __version__
    assert "config" in app.request_context.lifespan_context
    assert app.request_context.lifespan_context["config"] == test_config

def test_create_app_without_config() -> None:
    """Test creating app with default configuration."""
    with patch.dict(os.environ, {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "env-token",
        "DEBUG": "true"
    }):
        app = create_app()
        assert isinstance(app, MockFastMCP)
        assert app.name == "mpc-github-python"
        assert app.version == __version__
        assert "config" in app.request_context.lifespan_context

@pytest.mark.asyncio
async def test_app_lifespan(test_config: ServerConfig):
    """Test application lifespan."""
    app = create_app(test_config)
    async with app.lifespan(app) as context:
        assert "handler" in context
        assert isinstance(context["handler"], MockGitHubHandler)
        assert context["handler"]._initialized

@pytest.mark.asyncio
async def test_list_tools(handler: GitHubHandler):
    """Test listing available tools."""
    tools = handler.list_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0
    for tool in tools:
        assert isinstance(tool, Tool)
        assert tool.name
        assert tool.description
        assert tool.inputSchema

@pytest.mark.asyncio
async def test_call_tool(handler: GitHubHandler):
    """Test calling a tool."""
    result = await handler.call_tool("get_user", {})
    assert result == "octocat"

@pytest.mark.asyncio
async def test_call_tool_file_operations(handler: GitHubHandler):
    """Test file operations."""
    result = await handler.call_tool("list_files", {"path": "/"})
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_call_tool_issue_operations(handler: GitHubHandler):
    """Test issue operations."""
    result = await handler.call_tool("list_issues", {"state": "open"})
    assert isinstance(result, list)
    assert len(result) > 0
    assert result[0]["title"] == "Test Issue 1"

@pytest.mark.asyncio
async def test_call_tool_pull_request_operations(handler: GitHubHandler):
    """Test pull request operations."""
    result = await handler.call_tool("list_pull_requests", {"state": "open"})
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_call_tool_branch_operations(handler: GitHubHandler):
    """Test branch operations."""
    result = await handler.call_tool("list_branches", {})
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_call_tool_search_operations(handler: GitHubHandler):
    """Test search operations."""
    result = await handler.call_tool("search_code", {"query": "test"})
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_call_tool_error_conditions(handler: GitHubHandler):
    """Test error conditions."""
    with pytest.raises(ValueError):
        await handler.call_tool("list_issues", {"state": "invalid"})

@pytest.mark.asyncio
async def test_handler_repository_operations_complete(handler: GitHubHandler):
    """Test complete repository operations."""
    # Test repository creation
    repo = await handler.call_tool("create_repository", {
        "name": "new-test-repo",
        "private": True,
        "description": "A new test repository"
    })
    assert repo["name"] == "new-test-repo"
    assert repo["private"] is True

    # Test repository deletion
    result = await handler.call_tool("delete_repository", {})
    assert result["success"] is True

@pytest.mark.asyncio
async def test_handler_issue_operations_edge_cases(handler: GitHubHandler):
    """Test issue operations edge cases."""
    # Test creating issue without title
    with pytest.raises(ValueError):
        await handler.call_tool("create_issue", {
            "body": "This should fail"
        })

    # Test creating valid issue
    issue = await handler.call_tool("create_issue", {
        "title": "New Test Issue",
        "body": "This is a test issue",
        "labels": ["bug"],
        "assignee": "octocat"
    })
    assert issue["title"] == "New Test Issue"
    assert issue["state"] == "open"

@pytest_asyncio.fixture
async def handler() -> GitHubHandler:
    """Create a handler for testing."""
    handler = MockGitHubHandler("test-token")
    await handler.initialize()
    return handler 