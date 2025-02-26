"""Tests for the issues module."""

import pytest
from unittest.mock import Mock, patch
from github.Issue import Issue as GithubIssue
from github.Repository import Repository as GithubRepository
from github.Label import Label as GithubLabel
from github.Milestone import Milestone as GithubMilestone
from github.GithubObject import NotSet
from mcp_pygithub.operations.issues import IssueManager, IssueConfig
from mcp_pygithub.common.auth import GitHubClientFactory

class MockGitHubClientFactory(GitHubClientFactory):
    """Mock implementation of GitHubClientFactory for testing."""
    
    def __init__(self, mock_client: Mock):
        self._mock_client = mock_client
        self._clients = {}
    
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
    mock = Mock()
    mock._Github__requester = Mock()
    return mock

@pytest.fixture
def mock_factory(mock_github: Mock) -> GitHubClientFactory:
    """Create a mock GitHub client factory."""
    return MockGitHubClientFactory(mock_github)

@pytest.fixture
def mock_repository() -> Mock:
    """Create a mock repository."""
    return Mock(spec=GithubRepository)

@pytest.fixture
def mock_issue() -> Mock:
    """Create a mock issue."""
    mock = Mock(spec=GithubIssue)
    mock.number = 1
    mock.title = "Test Issue"
    mock.body = "Test Body"
    mock.state = "open"
    return mock

@pytest.fixture
def issue_manager(mock_repository: Mock, mock_factory: GitHubClientFactory) -> IssueManager:
    """Create an issue manager instance."""
    return IssueManager(mock_repository, factory=mock_factory)

@pytest.mark.asyncio
async def test_get_issue(issue_manager: IssueManager, mock_repository: Mock, mock_issue: Mock) -> None:
    """Test getting an issue."""
    mock_repository.get_issue.return_value = mock_issue
    
    # Get issue
    issue = await issue_manager.get_issue(1)
    assert issue.number == 1
    assert issue.title == "Test Issue"
    
    # Verify calls
    mock_repository.get_issue.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_create_issue(issue_manager: IssueManager, mock_repository: Mock, mock_issue: Mock) -> None:
    """Test creating an issue."""
    mock_repository.create_issue.return_value = mock_issue
    
    # Create issue
    config = IssueConfig(
        title="Test Issue",
        body="Test Body",
        assignees=["user1"],
        labels=["bug"],
        milestone=1
    )
    issue = await issue_manager.create_issue(config)
    
    # Verify issue
    assert issue.number == 1
    assert issue.title == "Test Issue"
    
    # Verify calls
    mock_repository.create_issue.assert_called_once_with(
        title="Test Issue",
        body="Test Body",
        assignees=["user1"],
        labels=["bug"],
        milestone=1
    )

@pytest.mark.asyncio
async def test_update_issue(issue_manager: IssueManager, mock_repository: Mock, mock_issue: Mock) -> None:
    """Test updating an issue."""
    mock_repository.get_issue.return_value = mock_issue
    
    # Update issue
    config = IssueConfig(
        title="Updated Title",
        body="Updated Body",
        assignees=["user2"],
        labels=["enhancement"],
        milestone=2,
        state="closed"
    )
    issue = await issue_manager.update_issue(1, config)
    
    # Verify calls
    mock_repository.get_issue.assert_called_once_with(1)
    mock_issue.edit.assert_any_call(title="Updated Title")
    mock_issue.edit.assert_any_call(body="Updated Body")
    mock_issue.edit.assert_any_call(assignees=["user2"])
    mock_issue.edit.assert_any_call(labels=["enhancement"])
    mock_issue.edit.assert_any_call(milestone=2)
    mock_issue.edit.assert_any_call(state="closed")

@pytest.mark.asyncio
async def test_close_issue(issue_manager: IssueManager, mock_repository: Mock, mock_issue: Mock) -> None:
    """Test closing an issue."""
    mock_repository.get_issue.return_value = mock_issue
    
    # Close issue
    issue = await issue_manager.close_issue(1)
    
    # Verify calls
    mock_repository.get_issue.assert_called_once_with(1)
    mock_issue.edit.assert_called_once_with(state="closed")

@pytest.mark.asyncio
async def test_reopen_issue(issue_manager: IssueManager, mock_repository: Mock, mock_issue: Mock) -> None:
    """Test reopening an issue."""
    mock_repository.get_issue.return_value = mock_issue
    
    # Reopen issue
    issue = await issue_manager.reopen_issue(1)
    
    # Verify calls
    mock_repository.get_issue.assert_called_once_with(1)
    mock_issue.edit.assert_called_once_with(state="open")

@pytest.mark.asyncio
async def test_list_issues(issue_manager: IssueManager, mock_repository: Mock, mock_issue: Mock) -> None:
    """Test listing issues."""
    mock_repository.get_issues.return_value = [mock_issue]
    
    # List issues
    issues = await issue_manager.list_issues(
        state="open",
        labels=["bug"],
        assignee="user1",
        milestone=1
    )
    
    # Verify results
    assert len(issues) == 1
    assert issues[0].number == 1
    assert issues[0].title == "Test Issue"
    
    # Verify calls
    mock_repository.get_issues.assert_called_once_with(
        state="open",
        labels=["bug"],
        assignee="user1",
        milestone=1
    )

@pytest.mark.asyncio
async def test_add_labels(issue_manager: IssueManager, mock_repository: Mock, mock_issue: Mock) -> None:
    """Test adding labels to an issue."""
    mock_label = Mock(spec=GithubLabel)
    mock_label.name = "bug"
    mock_issue.add_to_labels.return_value = [mock_label]
    mock_repository.get_issue.return_value = mock_issue
    
    # Add labels
    labels = await issue_manager.add_labels(1, ["bug"])
    
    # Verify results
    assert len(labels) == 1
    assert labels[0].name == "bug"
    
    # Verify calls
    mock_repository.get_issue.assert_called_once_with(1)
    mock_issue.add_to_labels.assert_called_once_with("bug")

@pytest.mark.asyncio
async def test_remove_labels(issue_manager: IssueManager, mock_repository: Mock, mock_issue: Mock) -> None:
    """Test removing labels from an issue."""
    mock_repository.get_issue.return_value = mock_issue
    
    # Remove labels
    await issue_manager.remove_labels(1, ["bug"])
    
    # Verify calls
    mock_repository.get_issue.assert_called_once_with(1)
    mock_issue.remove_from_labels.assert_called_once_with("bug")

@pytest.mark.asyncio
async def test_set_milestone(issue_manager: IssueManager, mock_repository: Mock, mock_issue: Mock) -> None:
    """Test setting a milestone on an issue."""
    mock_milestone = Mock(spec=GithubMilestone)
    mock_milestone.number = 1
    mock_repository.get_issue.return_value = mock_issue
    
    # Set milestone
    issue = await issue_manager.set_milestone(1, mock_milestone)
    
    # Verify calls
    mock_repository.get_issue.assert_called_once_with(1)
    mock_issue.edit.assert_called_once_with(milestone=mock_milestone)

@pytest.mark.asyncio
async def test_add_assignees(issue_manager: IssueManager, mock_repository: Mock, mock_issue: Mock) -> None:
    """Test adding assignees to an issue."""
    mock_repository.get_issue.return_value = mock_issue
    
    # Add assignees
    issue = await issue_manager.add_assignees(1, ["user1", "user2"])
    
    # Verify calls
    mock_repository.get_issue.assert_called_once_with(1)
    mock_issue.add_to_assignees.assert_called_once_with("user1", "user2")

@pytest.mark.asyncio
async def test_remove_assignees(issue_manager: IssueManager, mock_repository: Mock, mock_issue: Mock) -> None:
    """Test removing assignees from an issue."""
    mock_repository.get_issue.return_value = mock_issue
    
    # Remove assignees
    issue = await issue_manager.remove_assignees(1, ["user1", "user2"])
    
    # Verify calls
    mock_repository.get_issue.assert_called_once_with(1)
    mock_issue.remove_from_assignees.assert_called_once_with("user1", "user2") 