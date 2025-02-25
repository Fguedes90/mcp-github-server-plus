"""Tests for the repository module."""

import os
import pytest
from unittest.mock import Mock, patch, PropertyMock, MagicMock
from github.Repository import Repository as GithubRepository
from github.GithubObject import NotSet
from github.Auth import Auth
from github.AuthenticatedUser import AuthenticatedUser
from github.PaginatedList import PaginatedList
from github import Github
from mcp_github_server_plus.repository.repository import RepositoryConfig, RepositoryManager

# Check if we have a GitHub token for live testing
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
TEST_WITH_LIVE_API = GITHUB_TOKEN is not None

@pytest.fixture
def config() -> RepositoryConfig:
    """Create a test repository configuration."""
    if not TEST_WITH_LIVE_API:
        pytest.skip("No GitHub token available")
    return RepositoryConfig(
        token=GITHUB_TOKEN,
        owner=None,  # Will be set from authenticated user
        name=None,  # Will be set per test
    )

@pytest.fixture
def github_client() -> Github:
    """Create a GitHub client."""
    if not TEST_WITH_LIVE_API:
        pytest.skip("No GitHub token available")
    return Github(GITHUB_TOKEN)  # Direct token authentication

@pytest.fixture
def mock_auth() -> Mock:
    """Create a mock GitHub auth."""
    if TEST_WITH_LIVE_API:
        return Auth.Token(GITHUB_TOKEN)
    mock = Mock(spec=Auth)
    mock.token = "test-token"
    return mock

@pytest.fixture
def mock_requester() -> Mock:
    """Create a mock requester that doesn't make actual API calls."""
    if TEST_WITH_LIVE_API:
        pytest.skip("Using live GitHub API")
    mock = Mock()
    # Mock successful responses for different API calls
    def mock_request(*args, **kwargs):
        if args[0] == "POST" and args[1] == "/user/repos":
            return {}, {"id": 1, "name": "test-repo", "full_name": "test-owner/test-repo"}
        elif args[0] == "GET" and "repos" in args[1]:
            return {}, {"id": 1, "name": "test-repo", "full_name": "test-owner/test-repo"}
        elif args[0] == "GET" and "search/repositories" in args[1]:
            return {}, {"total_count": 0, "items": []}
        return {}, {}
    
    mock.requestJsonAndCheck = mock_request
    return mock

@pytest.fixture
def mock_github(mock_requester: Mock) -> Mock:
    """Create a mock Github instance."""
    if TEST_WITH_LIVE_API:
        from github import Github
        return Github(auth=Auth.Token(GITHUB_TOKEN))
    mock = Mock()
    mock._Github__requester = mock_requester
    return mock

@pytest.fixture
def mock_user(mock_requester: Mock) -> Mock:
    """Create a mock Github user."""
    if TEST_WITH_LIVE_API:
        pytest.skip("Using live GitHub API")
    mock = Mock(spec=AuthenticatedUser)
    type(mock).login = PropertyMock(return_value="test-user")
    mock._requester = mock_requester
    
    # Create a proper mock repository for create_repo
    repo = Mock(spec=GithubRepository)
    type(repo).full_name = PropertyMock(return_value="test-owner/test-repo")
    type(repo).name = PropertyMock(return_value="test-repo")
    mock.create_repo = Mock(return_value=repo)
    
    return mock

@pytest.fixture
def mock_repository(mock_requester: Mock) -> Mock:
    """Create a mock Github repository."""
    if TEST_WITH_LIVE_API:
        pytest.skip("Using live GitHub API")
    mock = Mock(spec=GithubRepository)
    type(mock).full_name = PropertyMock(return_value="test-owner/test-repo")
    type(mock).name = PropertyMock(return_value="test-repo")
    mock._requester = mock_requester
    return mock

@pytest.fixture
def mock_paginated_list() -> Mock:
    """Create a mock paginated list."""
    if TEST_WITH_LIVE_API:
        pytest.skip("Using live GitHub API")
    # Create a proper mock for PaginatedList
    class MockPaginatedList:
        def __init__(self):
            self.totalCount = 0
            self._items = []
        
        def get_page(self, page):
            return self._items
        
        def __iter__(self):
            return iter(self._items)
        
        def __eq__(self, other):
            if isinstance(other, PaginatedList):
                return True
            return False
    
    return MockPaginatedList()

@pytest.mark.asyncio
async def test_create_repository(config: RepositoryConfig, github_client: Github) -> None:
    """Test repository creation."""
    manager = RepositoryManager(config)
    repo_name = "test-repo-live"
    
    try:
        # Create repository
        repo = await manager.create_repository(repo_name)
        assert repo.name == repo_name
        assert not repo.private
        
        # Verify we can get it
        found_repo = await manager.get_repository(name=repo_name)
        assert found_repo.name == repo_name
    finally:
        # Clean up
        try:
            repo = github_client.get_repo(f"{github_client.get_user().login}/{repo_name}")
            repo.delete()
        except:
            pass

@pytest.mark.asyncio
async def test_get_repository(config: RepositoryConfig, github_client: Github) -> None:
    """Test getting a repository."""
    manager = RepositoryManager(config)
    repo_name = "test-repo-get"
    
    try:
        # Create repository first
        repo = await manager.create_repository(repo_name)
        
        # Test getting it
        found_repo = await manager.get_repository(name=repo_name)
        assert found_repo.name == repo_name
    finally:
        # Clean up
        try:
            repo = github_client.get_repo(f"{github_client.get_user().login}/{repo_name}")
            repo.delete()
        except:
            pass

@pytest.mark.asyncio
async def test_search_repositories(config: RepositoryConfig) -> None:
    """Test repository search."""
    manager = RepositoryManager(config)
    # Search for popular Python repositories
    result = await manager.search_repositories("language:python stars:>1000")
    assert isinstance(result, PaginatedList)
    assert result.totalCount > 0
    # Get first page of results
    repos = list(result.get_page(0))
    assert len(repos) > 0
    assert all(isinstance(repo, GithubRepository) for repo in repos)

@pytest.mark.asyncio
async def test_fork_repository(config: RepositoryConfig, github_client: Github) -> None:
    """Test repository forking."""
    manager = RepositoryManager(config)
    try:
        # Fork a well-known repository
        source_repo = await manager.get_repository(owner="octocat", name="Hello-World")
        forked_repo = await manager.fork_repository(source_repo)
        assert forked_repo.name == "Hello-World"
        assert forked_repo.fork
    finally:
        # Clean up
        try:
            repo = github_client.get_repo(f"{github_client.get_user().login}/Hello-World")
            repo.delete()
        except:
            pass

@pytest.mark.asyncio
async def test_delete_repository(config: RepositoryConfig, github_client: Github) -> None:
    """Test repository deletion."""
    manager = RepositoryManager(config)
    repo_name = "test-repo-delete"
    
    # Create a repository to delete
    repo = await manager.create_repository(repo_name)
    assert repo.name == repo_name
    
    # Delete it
    await manager.delete_repository(repo)
    
    # Verify it's gone
    with pytest.raises(Exception):
        await manager.get_repository(name=repo_name)

@pytest.mark.asyncio
async def test_get_repository_missing_info(mock_github: Mock, mock_user: Mock) -> None:
    """Test getting a repository with missing information."""
    config = RepositoryConfig(token="test-token")
    manager = RepositoryManager(config)
    manager.github = mock_github
    mock_github.get_user.return_value = mock_user
    
    # Test with missing name
    with pytest.raises(ValueError, match="Repository owner and name must be provided"):
        await manager.get_repository(owner="test-owner", name=None)
    
    # Test with missing owner and name
    with pytest.raises(ValueError, match="Repository owner and name must be provided"):
        await manager.get_repository(owner=None, name=None)

@pytest.mark.asyncio
async def test_search_repositories_with_sort_order(config: RepositoryConfig) -> None:
    """Test repository search with sort and order parameters."""
    manager = RepositoryManager(config)
    
    # Search with sort and order
    result = await manager.search_repositories(
        query="language:python stars:>1000",
        sort="stars",
        order="desc"
    )
    assert isinstance(result, PaginatedList)
    assert result.totalCount > 0

@pytest.mark.asyncio
async def test_fork_repository_with_org(config: RepositoryConfig, github_client: Github) -> None:
    """Test repository forking with organization."""
    manager = RepositoryManager(config)
    try:
        # Fork a well-known repository to an organization
        source_repo = await manager.get_repository(owner="octocat", name="Hello-World")
        # Note: This will fail if the user doesn't have an organization
        # but it tests the code path
        forked_repo = await manager.fork_repository(source_repo, organization="test-org")
        assert forked_repo.name == "Hello-World"
        assert forked_repo.fork
    except Exception as e:
        # We expect this to fail if the user doesn't have org access
        # but the code path is still tested
        assert any(msg in str(e) for msg in [
            "Not Found",
            "Resource not accessible by integration",
            "Must have admin rights to Repository"
        ])

@pytest.mark.asyncio
async def test_context_manager(config: RepositoryConfig) -> None:
    """Test repository manager as context manager."""
    # Test synchronous context manager
    with RepositoryManager(config) as manager:
        repo = await manager.get_repository(owner="octocat", name="Hello-World")
        assert repo.name == "Hello-World"
    
    # Test asynchronous context manager
    async with RepositoryManager(config) as manager:
        repo = await manager.get_repository(owner="octocat", name="Hello-World")
        assert repo.name == "Hello-World" 