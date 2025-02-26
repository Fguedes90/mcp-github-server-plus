"""Additional tests to improve coverage for the repository module."""

import pytest
import asyncio
from unittest.mock import Mock, patch, PropertyMock, MagicMock, AsyncMock
from github.Repository import Repository as GithubRepository
from github.GithubObject import NotSet
from github import Github
from typing import Dict, Any

from mcp_pygithub.operations.repository import (
    RepositoryConfig, 
    RepositoryManager, 
    SearchRepositoryConfig
)
from mcp_pygithub.common.auth import GitHubClientFactory
from mcp_pygithub.common.errors import RepositoryError

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
    mock = Mock(spec=Mock)
    type(mock).login = PropertyMock(return_value="test-user")
    
    # Create a proper mock repository for create_repo
    repo = Mock(spec=GithubRepository)
    type(repo).full_name = PropertyMock(return_value="test-owner/test-repo")
    type(repo).name = PropertyMock(return_value="test-repo")
    mock.create_repo = Mock(return_value=repo)
    mock.get_repo = Mock(return_value=repo)
    
    return mock

@pytest.fixture
def mock_branch() -> Mock:
    """Create a mock branch."""
    mock = Mock()
    mock.name = "main"
    mock.protected = False
    
    mock_commit = Mock()
    mock_commit.sha = "sha123"
    mock.commit = mock_commit
    
    return mock

@pytest.mark.asyncio
async def test_create_repository_with_mock_branches(
    mock_github: Mock,
    mock_user: Mock,
    mock_factory: GitHubClientFactory
) -> None:
    """Test repository creation with mock branches (covers lines 106-114)."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    mock_repo = Mock(spec=GithubRepository)
    type(mock_repo).name = PropertyMock(return_value="test-repo")
    
    # Set _branches attribute to trigger the mock initialization
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
    assert "_branches" in repo.__dict__
    assert "main" in repo._branches
    assert hasattr(repo._branches["main"], "commit")
    assert hasattr(repo, "_commits")

@pytest.mark.asyncio
async def test_get_repository_missing_values(
    mock_github: Mock,
    mock_user: Mock,
    mock_factory: GitHubClientFactory
) -> None:
    """Test getting a repository with missing values (covers line 138)."""
    # Create config with no name so the repository manager has to rely on parameters
    config = RepositoryConfig(token="test-token", name="test-repo", owner=None)
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Override name to None to force the error
    manager.config.name = None
    
    # Mock user login to be None to ensure both owner and name resolve to None
    mock_user.login = None
    mock_github.get_user.return_value = mock_user
    
    # Test with missing name and owner
    with pytest.raises(ValueError) as excinfo:
        await manager.get_repository()
    
    assert "Repository owner and name must be provided" in str(excinfo.value)

@pytest.mark.asyncio
async def test_search_repositories_with_per_page(
    mock_github: Mock,
    mock_factory: GitHubClientFactory
) -> None:
    """Test repository search with per_page parameter (covers lines 172, 187, 189)."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Create mock repositories
    mock_repos = []
    for i in range(10):
        repo = Mock(spec=GithubRepository)
        repo.name = f"test-repo-{i}"
        mock_repos.append(repo)
    
    # Set up mock paginated list properly
    mock_paginated_list = Mock()
    # Add the iterator method properly
    mock_paginated_list.__iter__ = Mock(return_value=iter(mock_repos))
    mock_github.search_repositories.return_value = mock_paginated_list
    
    # Test with per_page parameter
    search_config = SearchRepositoryConfig(
        query="test-query",
        per_page=5
    )
    
    results = await manager.search_repositories(search_config)
    
    # Verify results - should only return 5 repos due to per_page
    assert len(results) == 5
    mock_github.search_repositories.assert_called_once_with(
        query="test-query", 
        sort=NotSet, 
        order=NotSet
    )

@pytest.mark.asyncio
async def test_create_branch_success(
    mock_github: Mock,
    mock_user: Mock,
    mock_factory: GitHubClientFactory
) -> None:
    """Test branch creation (covers lines 289-327)."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    mock_repo = Mock(spec=GithubRepository)
    type(mock_repo).name = PropertyMock(return_value="test-repo")
    mock_github.get_repo.return_value = mock_repo
    
    # Set up branch
    mock_branch = Mock()
    mock_branch.commit.sha = "source-sha"
    mock_repo.get_branch = Mock(return_value=mock_branch)
    
    # Set up reference creation
    mock_ref = Mock()
    mock_ref_object = Mock()
    mock_ref_object.sha = "new-sha"
    mock_ref.object = mock_ref_object
    mock_repo.create_git_ref = Mock(return_value=mock_ref)
    
    # Create branch
    result = await manager.create_branch(name="new-branch", source="main")
    
    # Verify result
    assert result["name"] == "new-branch"
    assert result["sha"] == "new-sha"
    mock_repo.create_git_ref.assert_called_once_with("refs/heads/new-branch", "source-sha")

@pytest.mark.asyncio
async def test_create_branch_mock_repo(
    mock_github: Mock,
    mock_user: Mock,
    mock_factory: GitHubClientFactory
) -> None:
    """Test branch creation with a mock repository (covers lines 300-312)."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    mock_repo = Mock(spec=GithubRepository)
    type(mock_repo).name = PropertyMock(return_value="test-repo")
    mock_github.get_repo.return_value = mock_repo
    
    # Set up mock branches
    mock_repo._branches = {}
    
    # Create branch
    result = await manager.create_branch(name="new-branch", source="main")
    
    # Verify result
    assert result["name"] == "new-branch"
    assert "sha" in result
    assert "new-branch" in mock_repo._branches

@pytest.mark.asyncio
async def test_create_branch_error(
    mock_github: Mock,
    mock_user: Mock,
    mock_factory: GitHubClientFactory
) -> None:
    """Test branch creation failure (covers line 239)."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    mock_repo = Mock(spec=GithubRepository)
    type(mock_repo).name = PropertyMock(return_value="test-repo")
    mock_github.get_repo.return_value = mock_repo
    
    # Set up branch
    mock_branch = Mock()
    mock_branch.commit.sha = "source-sha"
    mock_repo.get_branch = Mock(return_value=mock_branch)
    
    # Set up reference creation to fail
    mock_repo.create_git_ref = Mock(side_effect=Exception("Reference already exists"))
    
    # Create branch
    with pytest.raises(RepositoryError) as excinfo:
        await manager.create_branch(name="new-branch", source="main")
    
    assert "Failed to create branch" in str(excinfo.value)

@pytest.mark.asyncio
async def test_create_branch_commit_fallback(
    mock_github: Mock,
    mock_user: Mock,
    mock_factory: GitHubClientFactory
) -> None:
    """Test branch creation with commit fallback."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    mock_repo = Mock(spec=GithubRepository)
    type(mock_repo).name = PropertyMock(return_value="test-repo")
    mock_github.get_repo.return_value = mock_repo
    
    # Set up branch to throw exception
    mock_repo.get_branch = Mock(side_effect=Exception("Branch not found"))
    
    # Set up commit
    mock_commit = Mock()
    mock_commit.sha = "commit-sha"
    mock_repo.get_commit = Mock(return_value=mock_commit)
    
    # Set up reference creation
    mock_ref = Mock()
    mock_ref_object = Mock()
    mock_ref_object.sha = "new-sha"
    mock_ref.object = mock_ref_object
    mock_repo.create_git_ref = Mock(return_value=mock_ref)
    
    # Create branch
    result = await manager.create_branch(name="new-branch", source="main")
    
    # Verify result
    assert result["name"] == "new-branch"
    assert result["sha"] == "new-sha"
    mock_repo.create_git_ref.assert_called_once_with("refs/heads/new-branch", "commit-sha")

@pytest.mark.asyncio
async def test_create_branch_direct_sha(
    mock_github: Mock,
    mock_user: Mock,
    mock_factory: GitHubClientFactory
) -> None:
    """Test branch creation with direct SHA."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    mock_repo = Mock(spec=GithubRepository)
    type(mock_repo).name = PropertyMock(return_value="test-repo")
    mock_github.get_repo.return_value = mock_repo
    
    # Set up both branch and commit to fail
    mock_repo.get_branch = Mock(side_effect=Exception("Branch not found"))
    mock_repo.get_commit = Mock(side_effect=Exception("Commit not found"))
    
    # Set up reference creation
    mock_ref = Mock()
    mock_ref_object = Mock()
    mock_ref_object.sha = "new-sha" 
    mock_ref.object = mock_ref_object
    mock_repo.create_git_ref = Mock(return_value=mock_ref)
    
    # Create branch with SHA
    result = await manager.create_branch(name="new-branch", source="abcdef1234567890")
    
    # Verify result
    assert result["name"] == "new-branch"
    assert result["sha"] == "new-sha"
    mock_repo.create_git_ref.assert_called_once_with("refs/heads/new-branch", "abcdef1234567890")

@pytest.mark.asyncio
async def test_list_branches(
    mock_github: Mock,
    mock_user: Mock,
    mock_factory: GitHubClientFactory
) -> None:
    """Test listing branches (covers list_branches method)."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    mock_repo = Mock(spec=GithubRepository)
    type(mock_repo).name = PropertyMock(return_value="test-repo")
    mock_github.get_repo.return_value = mock_repo
    
    # Set up branches
    mock_branch1 = Mock()
    mock_branch1.name = "main"
    mock_branch1.protected = False
    mock_branch1.commit.sha = "sha1"
    
    mock_branch2 = Mock()
    mock_branch2.name = "develop"
    mock_branch2.protected = True
    mock_branch2.commit.sha = "sha2"
    
    mock_repo.get_branches.return_value = [mock_branch1, mock_branch2]
    
    # List branches
    branches = await manager.list_branches()
    
    # Verify result
    assert len(branches) == 2
    assert branches[0]["name"] == "main"
    assert not branches[0]["protected"]
    assert branches[1]["name"] == "develop"
    assert branches[1]["protected"]
    
    # Test with protected filter
    branches = await manager.list_branches(protected=True)
    
    # Verify result
    assert len(branches) == 1
    assert branches[0]["name"] == "develop"

@pytest.mark.asyncio
async def test_list_branches_mock_repo(
    mock_github: Mock,
    mock_user: Mock,
    mock_factory: GitHubClientFactory
) -> None:
    """Test listing branches with a mock repository."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    manager = RepositoryManager(config, factory=mock_factory)
    
    # Set up mocks
    mock_github.get_user.return_value = mock_user
    mock_repo = Mock(spec=GithubRepository)
    type(mock_repo).name = PropertyMock(return_value="test-repo")
    mock_github.get_repo.return_value = mock_repo
    
    # Set up branches
    mock_repo._branches = {
        "main": {"name": "main", "protected": False, "commit": {"sha": "sha1"}},
        "develop": {"name": "develop", "protected": True, "commit": {"sha": "sha2"}}
    }
    
    # List branches
    branches = await manager.list_branches()
    
    # Verify result
    assert len(branches) == 2
    
    # Test with protected filter
    branches = await manager.list_branches(protected=True)
    
    # Verify result
    assert len(branches) == 1
    assert branches[0]["name"] == "develop"

def test_context_manager_sync(
    mock_github: Mock,
    mock_user: Mock,
    mock_factory: GitHubClientFactory
) -> None:
    """Test synchronous context manager (covers lines 259-262)."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    
    with RepositoryManager(config, factory=mock_factory) as manager:
        assert isinstance(manager, RepositoryManager)

@pytest.mark.asyncio
async def test_context_manager_async(
    mock_github: Mock,
    mock_user: Mock,
    mock_factory: GitHubClientFactory
) -> None:
    """Test asynchronous context manager (covers lines 264-267)."""
    config = RepositoryConfig(token="test-token", name="test-repo")
    
    async with RepositoryManager(config, factory=mock_factory) as manager:
        assert isinstance(manager, RepositoryManager) 