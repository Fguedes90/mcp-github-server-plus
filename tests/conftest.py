"""Pytest configuration and fixtures for all tests."""

import os
import pytest
import pytest_asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, Optional, Any
from github import Github, Auth
from mcp_pygithub.common.auth import GitHubClientFactory
from mcp_pygithub.common.types import ServerConfig
from github.Repository import Repository
from github.NamedUser import NamedUser
from github.Workflow import Workflow
from github.WorkflowRun import WorkflowRun

from mcp_pygithub.operations.actions import ActionManager
from mcp_pygithub.server.handlers import GitHubHandler

class DictLikeMock(MagicMock):
    """A mock that behaves like a dictionary."""
    def __getitem__(self, key):
        return self.__getattr__(key)

def create_mock_github_client() -> Mock:
    """Create a mock GitHub client with necessary attributes."""
    mock_client = Mock(spec=Github)
    
    # Create a mock user
    mock_user = Mock(spec=NamedUser)
    mock_user.login = "octocat"
    mock_user.name = "The Octocat"
    mock_user.email = "octocat@github.com"
    
    # Create a mock repository
    mock_repo = Mock(spec=Repository)
    mock_repo.name = "test-repo"
    mock_repo.private = True
    mock_repo.description = "Test repository"
    mock_repo.default_branch = "main"
    mock_repo.owner = mock_user
    
    # Set up common methods
    mock_client.get_user = Mock(return_value=mock_user)
    mock_client.get_repo = Mock(return_value=mock_repo)
    
    # Mock the requester to prevent real HTTP requests
    mock_requester = Mock()
    mock_requester.requestJsonAndCheck = Mock(return_value=({}, {}))
    mock_client._Github__requester = mock_requester
    
    return mock_client

class MockGitHubClientFactory(GitHubClientFactory):
    """Mock factory for creating GitHub clients."""
    def __init__(self, mock_client: Optional[Mock] = None):
        self._mock_client = mock_client or create_mock_github_client()
        self._cache: Dict[str, Mock] = {}

    def create_client(self, token: str) -> Mock:
        """Create a mock GitHub client."""
        if token not in self._cache:
            # Create a new mock client for each token
            mock_client = create_mock_github_client()
            # Store the token for verification
            mock_client._token = token
            self._cache[token] = mock_client
        return self._cache[token]

    def clear_cache(self) -> None:
        """Clear the client cache."""
        self._cache.clear()

@pytest.fixture
def mock_github_client() -> Mock:
    """Provide a mock GitHub client."""
    return create_mock_github_client()

@pytest.fixture
def mock_github_factory(mock_github_client: Mock) -> MockGitHubClientFactory:
    """Provide a mock GitHub client factory."""
    return MockGitHubClientFactory(mock_github_client)

@pytest.fixture
def github_token() -> str:
    """Get GitHub token from environment or return test token."""
    return os.getenv("GITHUB_TOKEN", "test-token")

@pytest.fixture
def server_config(github_token: str) -> ServerConfig:
    """Create server configuration with test settings."""
    return ServerConfig(
        host="localhost",
        port=8000,
        github_token=github_token,
        repository_owner="octocat",
        repository_name="test-repo"
    )

@pytest.fixture
def mock_workflow() -> MagicMock:
    """Create a mock workflow.
    
    This fixture provides a mock GitHub workflow with common attributes
    and methods set up for testing.
    """
    workflow = MagicMock(spec=Workflow)
    workflow.id = 123
    workflow.path = "test.yml"
    workflow.state = "active"
    workflow.name = "Test Workflow"
    workflow.create_dispatch = MagicMock(return_value=True)
    return workflow

@pytest.fixture
def mock_workflow_run() -> MagicMock:
    """Create a mock workflow run.
    
    This fixture provides a mock GitHub workflow run with common attributes
    and methods set up for testing.
    """
    run = MagicMock(spec=WorkflowRun)
    run.id = 456
    run.status = "completed"
    run.conclusion = "success"
    run.event = "push"
    run.head_branch = "main"
    run.download_logs = MagicMock(return_value=b"test logs")
    run.cancel = MagicMock(return_value=True)
    return run

@pytest.fixture
def mock_repository() -> MagicMock:
    """Create a mock repository.
    
    This fixture provides a mock GitHub repository with common attributes
    and methods set up for testing.
    """
    repo = MagicMock(spec=Repository)
    repo.default_branch = "main"
    repo.name = "test-repo"
    repo.full_name = "octocat/test-repo"
    return repo

@pytest.fixture
def mock_factory(mock_repository: MagicMock) -> GitHubClientFactory:
    """Create a mock GitHub client factory.
    
    This fixture provides a mock factory that returns consistent mock clients
    for testing.
    """
    return MockGitHubClientFactory(mock_repository)

@pytest.fixture
def action_manager(mock_repository: MagicMock, mock_factory: GitHubClientFactory) -> ActionManager:
    """Create an action manager for testing.
    
    This fixture provides a pre-configured action manager with mock dependencies
    for testing GitHub Actions operations.
    """
    return ActionManager(mock_repository, mock_factory)

@pytest_asyncio.fixture
async def handler(mock_repository: MagicMock) -> GitHubHandler:
    """Create a GitHub handler for testing.
    
    This fixture provides a pre-initialized handler with mock dependencies
    for testing the handler interface.
    """
    handler = GitHubHandler("test_token")
    handler._repository = mock_repository
    handler._actions = ActionManager(mock_repository)
    handler._initialized = True
    return handler

@pytest.fixture(autouse=True)
def mock_github_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Automatically mock GitHub authentication for all tests."""
    def mock_auth(*args: Any, **kwargs: Any) -> Mock:
        auth = Mock(spec=Auth)
        auth.token = kwargs.get("token", "test-token")
        return auth
    
    # Mock both the Auth.Token constructor and the Github class
    monkeypatch.setattr(Auth, "Token", mock_auth)
    monkeypatch.setattr("github.Github", create_mock_github_client)
    
    # Also patch the get_repo method to return our mock repository
    def mock_get_repo(self, full_name_or_id: str, **kwargs: Any) -> Mock:
        mock_repo = Mock(spec=Repository)
        mock_repo.name = full_name_or_id.split("/")[-1]
        mock_repo.owner = Mock(spec=NamedUser)
        mock_repo.owner.login = full_name_or_id.split("/")[0]
        return mock_repo
    
    monkeypatch.setattr(Github, "get_repo", mock_get_repo) 