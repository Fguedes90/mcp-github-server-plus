"""Tests for the repository module."""

import os
import pytest
from unittest.mock import Mock, patch, PropertyMock, MagicMock, AsyncMock
from github.Repository import Repository as GithubRepository
from github.GithubObject import NotSet
from github.Auth import Auth
from github.AuthenticatedUser import AuthenticatedUser
from github.PaginatedList import PaginatedList
from github import Github
from mcp_pygithub.operations.repository import RepositoryConfig, RepositoryManager
from mcp_pygithub.common.auth import GitHubClientFactory

# Check if we have a GitHub token for live testing
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
TEST_WITH_LIVE_API = GITHUB_TOKEN is not None

class MockGitHubClientFactory(GitHubClientFactory):
    """Mock implementation of GitHubClientFactory for testing."""
    
    def __init__(self, mock_client: Mock):
        self._mock_client = mock_client
        self._clients: Dict[str, Mock] = {}
    
    def create_client(self, token: str) -> Mock:
        """Return a mock client."""
        if token not in self._clients:
            self._clients[token] = self._mock_client
        return self._clients[token]
    
    def clear_cache(self) -> None:
        """Clear the mock client cache."""
        self._clients.clear()

@pytest.fixture
def config() -> RepositoryConfig:
    """Create a test repository configuration."""
    if not TEST_WITH_LIVE_API:
        pytest.skip("No GitHub token available")
    return RepositoryConfig(
        token=GITHUB_TOKEN,
        owner=None,  # Will be set from authenticated user
        name="test-repo"  # Default name that will be overridden in tests
    )

@pytest.fixture
def mock_github() -> Mock:
    """Create a mock Github instance."""
    mock = Mock(spec=Github)
    mock._Github__requester = Mock()
    return mock

@pytest.fixture
def mock_factory(mock_github: Mock) -> GitHubClientFactory:
    """Create a mock GitHub client factory."""
    return MockGitHubClientFactory(mock_github)

@pytest.fixture
def mock_user() -> Mock:
    """Create a mock Github user."""
    mock = Mock(spec=AuthenticatedUser)
    type(mock).login = PropertyMock(return_value="test-user")
    
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
    mock = Mock(spec=PaginatedList)
    mock.totalCount = 100
    
    # Create mock repositories
    mock_repos = []
    for i in range(5):
        repo = Mock(spec=GithubRepository)
        repo.name = f"test-repo-{i}"
        repo.full_name = f"test-owner/test-repo-{i}"
        mock_repos.append(repo)
    
    mock.get_page = Mock(return_value=mock_repos)
    mock.__iter__ = Mock(return_value=iter(mock_repos))
    mock.__getitem__ = Mock(side_effect=lambda i: mock_repos[i] if i < len(mock_repos) else None)
    return mock

@pytest.mark.asyncio
async def test_create_repository(mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test repository creation."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    mock_repo = Mock(spec=GithubRepository)
    mock_repo.name = "test-repo"
    mock_repo.private = True
    mock_repo.description = "Test repository"
    
    # Set up create_repo mock
    mock_user.create_repo = Mock(return_value=mock_repo)
    
    # Create repository
    repo = await manager.create_repository(
        name="test-repo",
        private=True,
        description="Test repository"
    )
    
    # Verify result
    assert repo == mock_repo
    
    # Verify calls
    mock_github.get_user.assert_called_once()
    mock_user.create_repo.assert_called_once_with(
        "test-repo",
        description="Test repository",
        private=True
    )

@pytest.mark.asyncio
async def test_get_repository(config: RepositoryConfig, mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test getting a repository."""
    mock_github.get_user.return_value = mock_user
    
    # Create mock repository
    mock_repo = Mock(spec=GithubRepository)
    mock_repo.name = "test-repo"
    mock_github.get_repo.return_value = mock_repo
    
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Test getting repository
    repo = await manager.get_repository(name="test-repo")
    assert repo.name == "test-repo"
    mock_github.get_repo.assert_called_once_with("test-user/test-repo")

@pytest.mark.asyncio
async def test_search_repositories(mock_github: Mock, mock_paginated_list: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test repository search."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.search_repositories.return_value = mock_paginated_list
    mock_paginated_list.__iter__.return_value = iter([mock_repository])
    
    # Search repositories
    results = await manager.search_repositories("test query")
    
    # Verify results
    assert len(results) == 1
    assert results[0] == mock_repository
    
    # Verify calls
    mock_github.search_repositories.assert_called_once_with(query="test query", sort=NotSet, order=NotSet)

@pytest.mark.asyncio
async def test_fork_repository(config: RepositoryConfig, mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test repository forking."""
    mock_github.get_user.return_value = mock_user
    
    # Create mock source repository
    mock_source_repo = Mock(spec=GithubRepository)
    type(mock_source_repo).name = PropertyMock(return_value="Hello-World")
    
    # Create mock forked repository
    mock_forked_repo = Mock(spec=GithubRepository)
    type(mock_forked_repo).name = PropertyMock(return_value="Hello-World")
    type(mock_forked_repo).fork = PropertyMock(return_value=True)
    mock_source_repo.create_fork.return_value = mock_forked_repo
    
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Fork repository
    forked_repo = await manager.fork_repository(mock_source_repo)
    assert forked_repo.name == "Hello-World"
    assert forked_repo.fork
    mock_source_repo.create_fork.assert_called_once_with(
        organization=NotSet,
        name=NotSet,
        default_branch_only=False
    )

@pytest.mark.asyncio
async def test_delete_repository(config: RepositoryConfig, mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test repository deletion."""
    mock_github.get_user.return_value = mock_user
    
    # Create mock repository
    mock_repo = Mock(spec=GithubRepository)
    mock_repo.name = "test-repo"
    
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Delete repository
    await manager.delete_repository(mock_repo)
    mock_repo.delete.assert_called_once()

@pytest.mark.asyncio
async def test_get_repository_missing_info(mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test getting a repository with missing information."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    mock_user.login = "test-user"
    
    # Get repository without owner
    repo = await manager.get_repository()
    
    # Verify calls
    mock_github.get_user.assert_called_once()
    mock_github.get_repo.assert_called_once_with("test-user/test-repo")

@pytest.mark.asyncio
async def test_search_repositories_with_sort_order(mock_github: Mock, mock_paginated_list: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test repository search with sort and order parameters."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.search_repositories.return_value = mock_paginated_list
    mock_paginated_list.__iter__.return_value = iter([mock_repository])
    
    # Search repositories with sort and order
    results = await manager.search_repositories("test query", sort="stars", order="desc")
    
    # Verify results
    assert len(results) == 1
    assert results[0] == mock_repository
    
    # Verify calls
    mock_github.search_repositories.assert_called_once_with(query="test query", sort="stars", order="desc")

@pytest.mark.asyncio
async def test_fork_repository_with_org(config: RepositoryConfig, mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test repository forking with organization."""
    mock_github.get_user.return_value = mock_user
    
    # Create mock source repository
    mock_source_repo = Mock(spec=GithubRepository)
    type(mock_source_repo).name = PropertyMock(return_value="Hello-World")
    
    # Create mock forked repository
    mock_forked_repo = Mock(spec=GithubRepository)
    type(mock_forked_repo).name = PropertyMock(return_value="Hello-World")
    type(mock_forked_repo).fork = PropertyMock(return_value=True)
    mock_source_repo.create_fork.return_value = mock_forked_repo
    
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Fork repository to organization
    forked_repo = await manager.fork_repository(mock_source_repo, organization="test-org")
    assert forked_repo.name == "Hello-World"
    assert forked_repo.fork
    mock_source_repo.create_fork.assert_called_once_with(
        organization="test-org",
        name=NotSet,
        default_branch_only=False
    )

@pytest.mark.asyncio
async def test_context_manager(config: RepositoryConfig, mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test repository manager as context manager."""
    mock_github.get_user.return_value = mock_user
    
    # Create mock repository
    mock_repo = Mock(spec=GithubRepository)
    type(mock_repo).name = PropertyMock(return_value="test-repo")
    mock_github.get_repo.return_value = mock_repo
    
    # Test synchronous context manager
    with RepositoryManager(config, factory=mock_factory) as manager:
        repo = await manager.get_repository(name="test-repo")
        assert repo.name == "test-repo"
        mock_github.get_repo.assert_called_once_with("test-user/test-repo")
    
    # Test asynchronous context manager
    async with RepositoryManager(config, factory=mock_factory) as manager:
        repo = await manager.get_repository(name="test-repo")
        assert repo.name == "test-repo"
        mock_github.get_repo.assert_called_with("test-user/test-repo")

@pytest.mark.asyncio
async def test_create_repository_with_mock_branch_setup(mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test repository creation with mock branch setup."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    mock_repo = Mock(spec=GithubRepository)
    mock_repo.name = "test-repo"
    mock_repo.private = True
    mock_repo.description = "Test repository"
    
    # Set _branches attribute to trigger mock branch setup
    mock_repo._branches = {}
    
    # Set up create_repo mock
    mock_user.create_repo = Mock(return_value=mock_repo)
    
    # Create repository
    repo = await manager.create_repository(
        name="test-repo",
        private=True,
        description="Test repository"
    )
    
    # Verify result
    assert repo == mock_repo
    
    # Verify branch was created
    assert "main" in repo._branches
    assert repo._branches["main"].name == "main"
    assert hasattr(repo._branches["main"], "commit")
    
    # Verify mock commit was created
    initial_sha = "aa218f56b14c9653891f9e74264a383fa43fefbd"
    assert initial_sha in repo._commits
    assert repo._commits[initial_sha].sha == initial_sha
    assert repo._branches["main"].commit == repo._commits[initial_sha]

@pytest.mark.asyncio
async def test_get_repository_missing_required_info(mock_github: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test getting a repository with both owner and name missing."""
    # Create config with a default name (required) but we'll test without providing one to get_repository
    config = RepositoryConfig(token="test-token", name="default-name")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mock user with no login
    mock_user = Mock()
    mock_user.login = None
    mock_github.get_user.return_value = mock_user
    
    # Test getting repository without owner or name
    with pytest.raises(ValueError, match="Repository owner and name must be provided"):
        await manager.get_repository(name=None, owner=None)

@pytest.mark.asyncio
async def test_search_repositories_with_pagination(mock_github: Mock, mock_paginated_list: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test repository search with pagination parameters."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.search_repositories.return_value = mock_paginated_list
    
    # Test with page parameter
    results = await manager.search_repositories("test query", page=2)
    
    # Verify results
    mock_github.search_repositories.assert_called_with(query="test query", sort=NotSet, order=NotSet)
    mock_paginated_list.get_page.assert_called_once_with(2)

@pytest.mark.asyncio
async def test_search_repositories_with_per_page(mock_github: Mock, mock_paginated_list: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test repository search with per_page parameter."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.search_repositories.return_value = mock_paginated_list
    
    # Create mock repositories
    mock_repos = []
    for i in range(10):
        repo = Mock(spec=GithubRepository)
        repo.name = f"test-repo-{i}"
        mock_repos.append(repo)
    
    # Configure the paginated list
    mock_paginated_list.__iter__.return_value = iter(mock_repos)
    
    # Test with per_page parameter
    results = await manager.search_repositories("test query", per_page=3)
    
    # Verify results
    assert len(results) == 3
    mock_github.search_repositories.assert_called_with(query="test query", sort=NotSet, order=NotSet)

@pytest.mark.asyncio
async def test_search_repositories_with_config_object(mock_github: Mock, mock_paginated_list: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test repository search with a config object."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.search_repositories.return_value = mock_paginated_list
    
    # Test with config object
    from mcp_pygithub.operations.repository import SearchRepositoryConfig
    search_config = SearchRepositoryConfig(
        query="test query",
        sort="stars",
        order="desc",
        page=None,
        per_page=None
    )
    
    results = await manager.search_repositories(search_config)
    
    # Verify results
    mock_github.search_repositories.assert_called_with(query="test query", sort="stars", order="desc") 

@pytest.mark.asyncio
async def test_delete_repository_by_name(mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test repository deletion by name."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    
    # Create mock repository
    mock_repo = Mock(spec=GithubRepository)
    mock_repo.name = "test-repo-to-delete"
    mock_user.get_repo.return_value = mock_repo
    
    # Delete repository by name
    await manager.delete_repository("test-repo-to-delete")
    
    # Verify calls
    mock_github.get_user.assert_called_once()
    mock_user.get_repo.assert_called_once_with("test-repo-to-delete")
    mock_repo.delete.assert_called_once()

@pytest.mark.asyncio
async def test_list_branches_mock_repository(mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test listing branches with a mock repository."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    
    # Create mock repository with _branches
    mock_repo = Mock(spec=GithubRepository)
    mock_repo.name = "test-repo"
    mock_repo._branches = {
        "main": {
            "name": "main",
            "protected": False,
            "commit": {"sha": "abc123"}
        },
        "develop": {
            "name": "develop",
            "protected": True,
            "commit": {"sha": "def456"}
        }
    }
    mock_github.get_repo.return_value = mock_repo
    
    # List branches
    branches = await manager.list_branches()
    
    # Verify results
    assert len(branches) == 2
    assert any(b["name"] == "main" for b in branches)
    assert any(b["name"] == "develop" for b in branches)
    
    # List protected branches
    protected_branches = await manager.list_branches(protected=True)
    
    # Verify results
    assert len(protected_branches) == 1
    assert protected_branches[0]["name"] == "develop"
    assert protected_branches[0]["protected"] == True

@pytest.mark.asyncio
async def test_list_branches_real_repository(mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test listing branches with a real repository."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    
    # Create mock repository without _branches
    mock_repo = Mock(spec=GithubRepository)
    mock_repo.name = "test-repo"
    
    # Create mock branches
    main_branch = Mock()
    main_branch.name = "main"
    main_branch.protected = False
    main_commit = Mock()
    main_commit.sha = "abc123"
    main_branch.commit = main_commit
    
    develop_branch = Mock()
    develop_branch.name = "develop"
    develop_branch.protected = True
    develop_commit = Mock()
    develop_commit.sha = "def456"
    develop_branch.commit = develop_commit
    
    branches = [main_branch, develop_branch]
    mock_repo.get_branches.return_value = branches
    mock_github.get_repo.return_value = mock_repo
    
    # List branches
    result = await manager.list_branches()
    
    # Verify results
    assert len(result) == 2
    assert any(b["name"] == "main" for b in result)
    assert any(b["name"] == "develop" for b in result)
    
    # List protected branches
    result = await manager.list_branches(protected=True)
    
    # Verify results
    assert len(result) == 1
    assert result[0]["name"] == "develop"
    assert result[0]["protected"] == True 

@pytest.mark.asyncio
async def test_create_branch_mock_repository(mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test creating a branch with a mock repository."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    
    # Create mock repository with _branches
    mock_repo = Mock(spec=GithubRepository)
    mock_repo.name = "test-repo"
    
    # Setup initial branches
    initial_sha = "aa218f56b14c9653891f9e74264a383fa43fefbd"
    mock_commit = Mock()
    mock_commit.sha = initial_sha
    
    mock_branch = Mock()
    mock_branch.name = "main"
    mock_branch.commit = mock_commit
    
    mock_repo._branches = {
        "main": mock_branch
    }
    
    mock_repo._commits = {
        initial_sha: mock_commit
    }
    
    mock_github.get_repo.return_value = mock_repo
    
    # Create a branch
    branch = await manager.create_branch("feature", "main")
    
    # Verify the result
    assert branch["name"] == "feature"
    assert branch["sha"] == "bb328f56c14d9653891f9e74264a383fa43fefcd"
    assert "feature" in mock_repo._branches

@pytest.mark.asyncio
async def test_create_branch_real_repository(mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test creating a branch with a real repository."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    
    # Create mock repository
    mock_repo = Mock(spec=GithubRepository)
    mock_repo.name = "test-repo"
    
    # Setup for get_branch (source branch)
    source_branch = Mock()
    source_commit = Mock()
    source_commit.sha = "aa218f56b14c9653891f9e74264a383fa43fefbd"
    source_branch.commit = source_commit
    mock_repo.get_branch.return_value = source_branch
    
    # Setup for create_git_ref
    ref_obj = Mock()
    ref_obj.object = Mock()
    ref_obj.object.sha = "bb328f56c14d9653891f9e74264a383fa43fefcd"
    mock_repo.create_git_ref.return_value = ref_obj
    
    mock_github.get_repo.return_value = mock_repo
    
    # Create a branch
    branch = await manager.create_branch("feature", "main")
    
    # Verify the result
    assert branch["name"] == "feature"
    assert branch["sha"] == "bb328f56c14d9653891f9e74264a383fa43fefcd"
    mock_repo.get_branch.assert_called_once_with("main")
    mock_repo.create_git_ref.assert_called_once_with(
        "refs/heads/feature", 
        "aa218f56b14c9653891f9e74264a383fa43fefbd"
    )

@pytest.mark.asyncio
async def test_create_branch_from_commit(mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test creating a branch from a commit SHA."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    
    # Create mock repository
    mock_repo = Mock(spec=GithubRepository)
    mock_repo.name = "test-repo"
    
    # Setup for get_branch to fail
    mock_repo.get_branch.side_effect = Exception("Branch not found")
    
    # Setup for get_commit
    commit = Mock()
    commit.sha = "aa218f56b14c9653891f9e74264a383fa43fefbd"
    mock_repo.get_commit.return_value = commit
    
    # Setup for create_git_ref
    ref_obj = Mock()
    ref_obj.object = Mock()
    ref_obj.object.sha = "bb328f56c14d9653891f9e74264a383fa43fefcd"
    mock_repo.create_git_ref.return_value = ref_obj
    
    mock_github.get_repo.return_value = mock_repo
    
    # Create a branch from commit SHA
    branch = await manager.create_branch("feature", "aa218f56b14c9653891f9e74264a383fa43fefbd")
    
    # Verify the result
    assert branch["name"] == "feature"
    assert branch["sha"] == "bb328f56c14d9653891f9e74264a383fa43fefcd"
    mock_repo.get_branch.assert_called_once()
    mock_repo.get_commit.assert_called_once_with("aa218f56b14c9653891f9e74264a383fa43fefbd")
    mock_repo.create_git_ref.assert_called_once_with(
        "refs/heads/feature", 
        "aa218f56b14c9653891f9e74264a383fa43fefbd"
    )

@pytest.mark.asyncio
async def test_create_branch_with_sha_fallback(mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test creating a branch with direct SHA fallback."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    
    # Create mock repository
    mock_repo = Mock(spec=GithubRepository)
    mock_repo.name = "test-repo"
    
    # Setup for get_branch to fail
    mock_repo.get_branch.side_effect = Exception("Branch not found")
    
    # Setup for get_commit to fail
    mock_repo.get_commit.side_effect = Exception("Commit not found")
    
    # Setup for create_git_ref
    ref_obj = Mock()
    ref_obj.object = Mock()
    ref_obj.object.sha = "bb328f56c14d9653891f9e74264a383fa43fefcd"
    mock_repo.create_git_ref.return_value = ref_obj
    
    mock_github.get_repo.return_value = mock_repo
    
    # Create a branch with SHA fallback
    branch = await manager.create_branch("feature", "aa218f56b14c9653891f9e74264a383fa43fefbd")
    
    # Verify the result
    assert branch["name"] == "feature"
    assert branch["sha"] == "bb328f56c14d9653891f9e74264a383fa43fefcd"
    mock_repo.get_branch.assert_called_once()
    mock_repo.get_commit.assert_called_once()
    mock_repo.create_git_ref.assert_called_once_with(
        "refs/heads/feature", 
        "aa218f56b14c9653891f9e74264a383fa43fefbd"
    )

@pytest.mark.asyncio
async def test_create_branch_error(mock_github: Mock, mock_user: Mock, mock_factory: GitHubClientFactory) -> None:
    """Test error handling when creating a branch."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    
    # Create mock repository
    mock_repo = Mock(spec=GithubRepository)
    mock_repo.name = "test-repo"
    
    # Setup for get_branch
    source_branch = Mock()
    source_commit = Mock()
    source_commit.sha = "aa218f56b14c9653891f9e74264a383fa43fefbd"
    source_branch.commit = source_commit
    mock_repo.get_branch.return_value = source_branch
    
    # Setup for create_git_ref to fail
    mock_repo.create_git_ref.side_effect = Exception("Failed to create reference")
    
    mock_github.get_repo.return_value = mock_repo
    
    # Create a branch with error
    from mcp_pygithub.common.errors import RepositoryError
    with pytest.raises(RepositoryError, match="Failed to create branch: Failed to create reference"):
        await manager.create_branch("feature", "main") 