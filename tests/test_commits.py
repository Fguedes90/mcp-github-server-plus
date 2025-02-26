"""Tests for the commits module."""

import pytest
from unittest.mock import Mock, patch, PropertyMock
from github.Repository import Repository as GithubRepository
from github.Commit import Commit
from github.GithubObject import NotSet
from github.Comparison import Comparison
from mcp_pygithub.operations.commits import CommitManager, CommitConfig, ListCommitsConfig

@pytest.fixture
def mock_repository() -> Mock:
    """Create a mock repository."""
    return Mock(spec=GithubRepository)

@pytest.fixture
def mock_commit() -> Mock:
    """Create a mock commit."""
    mock = Mock(spec=Commit)
    mock.sha = "test-sha"
    mock.commit.message = "Test commit"
    mock.commit.author.name = "Test Author"
    mock.commit.author.email = "test@example.com"
    mock.commit.committer.name = "Test Committer"
    mock.commit.committer.email = "test@example.com"
    return mock

@pytest.fixture
def commit_manager(mock_repository: Mock) -> CommitManager:
    """Create a commit manager instance."""
    return CommitManager(mock_repository)

@pytest.mark.asyncio
async def test_get_commit(commit_manager: CommitManager, mock_repository: Mock, mock_commit: Mock) -> None:
    """Test getting a commit by SHA."""
    mock_repository.get_commit.return_value = mock_commit
    
    # Get commit
    commit = await commit_manager.get_commit("test-sha")
    assert commit.sha == "test-sha"
    assert commit.commit.message == "Test commit"
    
    # Verify calls
    mock_repository.get_commit.assert_called_once_with("test-sha")

@pytest.mark.asyncio
async def test_list_commits_no_filters(commit_manager: CommitManager, mock_repository: Mock, mock_commit: Mock) -> None:
    """Test listing commits without filters."""
    mock_repository.get_commits.return_value = [mock_commit]
    
    # List commits
    config = ListCommitsConfig()
    commits = await commit_manager.list_commits(config)
    
    # Verify results
    assert len(commits) == 1
    assert commits[0].sha == "test-sha"
    
    # Verify calls
    mock_repository.get_commits.assert_called_once_with(
        sha=NotSet,
        path=NotSet,
    )

@pytest.mark.asyncio
async def test_list_commits_with_filters(commit_manager: CommitManager, mock_repository: Mock, mock_commit: Mock) -> None:
    """Test listing commits with filters."""
    # Create mock paginated list
    mock_paginated_list = Mock()
    mock_paginated_list.get_page.return_value = [mock_commit]
    mock_repository.get_commits.return_value = mock_paginated_list
    
    # List commits with filters
    config = ListCommitsConfig(
        branch="main",
        path="src",
        page=1,
        per_page=10
    )
    commits = await commit_manager.list_commits(config)
    
    # Verify results
    assert len(commits) == 1
    assert commits[0].sha == "test-sha"
    
    # Verify calls
    mock_repository.get_commits.assert_called_once_with(
        sha="main",
        path="src",
    )
    mock_paginated_list.get_page.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_compare_commits(commit_manager: CommitManager, mock_repository: Mock, mock_commit: Mock) -> None:
    """Test comparing commits."""
    # Create mock comparison
    mock_comparison = Mock(spec=Comparison)
    mock_comparison.ahead_by = 2
    mock_comparison.behind_by = 1
    mock_comparison.commits = [mock_commit, mock_commit]
    mock_repository.compare.return_value = mock_comparison
    
    # Compare commits
    result = await commit_manager.compare_commits("base-sha", "head-sha")
    
    # Verify results
    assert result["ahead_by"] == 2
    assert result["behind_by"] == 1
    assert len(result["commits"]) == 2
    assert all(commit.sha == "test-sha" for commit in result["commits"])
    
    # Verify calls
    mock_repository.compare.assert_called_once_with("base-sha", "head-sha") 