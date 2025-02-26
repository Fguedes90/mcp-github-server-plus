"""Tests for the branches module."""

import os
import uuid
import pytest
from unittest.mock import Mock, patch, PropertyMock
from github.Repository import Repository as GithubRepository
from github.Branch import Branch as GithubBranch
from github.GitRef import GitRef
from github.BranchProtection import BranchProtection
from github.GithubObject import NotSet
from github import Github
from mcp_pygithub.operations.repository import RepositoryConfig, RepositoryManager
from mcp_pygithub.operations.branches import BranchManager, BranchProtectionConfig
from mcp_pygithub.operations.files import FileManager
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
def mock_repository() -> Mock:
    """Create a mock repository."""
    mock = Mock(spec=GithubRepository)
    mock.default_branch = "main"
    return mock

@pytest.fixture
def mock_branch() -> Mock:
    """Create a mock branch."""
    mock = Mock(spec=GithubBranch)
    mock.name = "test-branch"
    mock.commit = Mock()
    mock.commit.sha = "test-sha"
    return mock

@pytest.fixture
def mock_git_ref() -> Mock:
    """Create a mock git ref."""
    mock = Mock(spec=GitRef)
    mock.ref = "refs/heads/test-branch"
    mock.object = Mock()
    mock.object.sha = "test-sha"
    return mock

@pytest.fixture
def branch_manager(mock_repository: Mock, mock_factory: GitHubClientFactory) -> BranchManager:
    """Create a branch manager instance."""
    return BranchManager(mock_repository, factory=mock_factory)

@pytest.mark.asyncio
async def test_get_branch(branch_manager: BranchManager, mock_repository: Mock, mock_branch: Mock) -> None:
    """Test getting a branch."""
    mock_repository.get_branch.return_value = mock_branch
    
    # Get branch
    branch = await branch_manager.get_branch("test-branch")
    assert branch.name == "test-branch"
    mock_repository.get_branch.assert_called_once_with("test-branch")

@pytest.mark.asyncio
async def test_get_branch_empty_repo(branch_manager: BranchManager, mock_repository: Mock, mock_branch: Mock) -> None:
    """Test getting a branch in an empty repository."""
    # Mock branch not found first time
    mock_repository.get_branch.side_effect = [
        Exception("Branch not found"),
        mock_branch
    ]
    
    # Mock empty commits list
    mock_repository.get_commits.return_value = []
    
    # Mock file creation
    mock_content = Mock()
    mock_content.sha = "test-sha"
    mock_repository.create_file.return_value = (mock_content, None)
    
    # Get branch
    branch = await branch_manager.get_branch("main")
    assert branch.name == "test-branch"
    
    # Verify file creation
    mock_repository.create_file.assert_called_once_with(
        path="README.md",
        message="Initial commit",
        content="# Repository\nInitialized by BranchManager",
        branch="main",
    )

@pytest.mark.asyncio
async def test_create_branch(branch_manager: BranchManager, mock_repository: Mock, mock_branch: Mock, mock_git_ref: Mock) -> None:
    """Test branch creation."""
    mock_repository.get_branch.return_value = mock_branch
    mock_repository.create_git_ref.return_value = mock_git_ref
    
    # Create branch
    branch = await branch_manager.create_branch("test-branch")
    assert branch.name == "test-branch"
    
    # Verify calls
    mock_repository.get_branch.assert_called_with("test-branch")
    mock_repository.create_git_ref.assert_called_once_with(
        ref="refs/heads/test-branch",
        sha="test-sha"
    )

@pytest.mark.asyncio
async def test_update_branch(branch_manager: BranchManager, mock_repository: Mock, mock_branch: Mock, mock_git_ref: Mock) -> None:
    """Test branch update."""
    mock_repository.get_git_ref.return_value = mock_git_ref
    mock_repository.get_branch.return_value = mock_branch
    
    # Update branch
    branch = await branch_manager.update_branch("test-branch", "new-sha", force=True)
    assert branch.name == "test-branch"
    
    # Verify calls
    mock_repository.get_git_ref.assert_called_once_with("heads/test-branch")
    mock_git_ref.edit.assert_called_once_with(sha="new-sha", force=True)

@pytest.mark.asyncio
async def test_delete_branch(branch_manager: BranchManager, mock_repository: Mock, mock_git_ref: Mock) -> None:
    """Test branch deletion."""
    mock_repository.get_git_ref.return_value = mock_git_ref
    
    # Delete branch
    await branch_manager.delete_branch("test-branch")
    
    # Verify calls
    mock_repository.get_git_ref.assert_called_once_with("heads/test-branch")
    mock_git_ref.delete.assert_called_once()

@pytest.mark.asyncio
async def test_protect_branch(branch_manager: BranchManager, mock_repository: Mock, mock_branch: Mock) -> None:
    """Test branch protection."""
    mock_repository.get_branch.return_value = mock_branch
    
    # Configure protection
    config = BranchProtectionConfig(
        required_status_checks=["test-status"],
        enforce_admins=True,
        required_pull_request_reviews=True,
        required_approving_review_count=1,
    )
    
    # Protect branch
    await branch_manager.protect_branch("test-branch", config)
    
    # Verify calls
    mock_repository.get_branch.assert_called_once_with("test-branch")
    mock_branch.edit_protection.assert_called_once_with(
        strict=True,
        contexts=["test-status"],
        enforce_admins=True,
        user_push_restrictions=NotSet,
        team_push_restrictions=NotSet,
        require_code_owner_reviews=False,
        required_approving_review_count=1,
        dismiss_stale_reviews=False,
    )

@pytest.mark.asyncio
async def test_remove_protection(branch_manager: BranchManager, mock_repository: Mock, mock_branch: Mock) -> None:
    """Test removing branch protection."""
    mock_repository.get_branch.return_value = mock_branch
    
    # Remove protection
    await branch_manager.remove_protection("test-branch")
    
    # Verify calls
    mock_repository.get_branch.assert_called_once_with("test-branch")
    mock_branch.remove_protection.assert_called_once()

@pytest.mark.asyncio
async def test_list_branches(branch_manager: BranchManager, mock_repository: Mock, mock_branch: Mock) -> None:
    """Test listing branches."""
    mock_repository.get_branches.return_value = [mock_branch]
    
    # List branches
    branches = await branch_manager.list_branches()
    assert len(branches) == 1
    assert branches[0].name == "test-branch"
    
    # Verify calls
    mock_repository.get_branches.assert_called_once() 