"""Tests for the pull requests module."""

import pytest
from unittest.mock import Mock, patch
from github.PullRequest import PullRequest as GithubPullRequest
from github.Repository import Repository as GithubRepository
from github.PullRequestReview import PullRequestReview
from github.GithubObject import NotSet
from mcp_pygithub.operations.pulls import PullRequestManager, PullRequestConfig
from mcp_pygithub.common.auth import GitHubClientFactory
from unittest.mock import AsyncMock

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
def mock_pull_request() -> Mock:
    """Create a mock pull request."""
    mock = Mock(spec=GithubPullRequest)
    mock.number = 1
    mock.title = "Test PR"
    mock.body = "Test Body"
    mock.head.ref = "feature"
    mock.base.ref = "main"
    mock.draft = False
    mock.maintainer_can_modify = True
    return mock

@pytest.fixture
def pull_request_manager(mock_repository: Mock, mock_factory: GitHubClientFactory) -> PullRequestManager:
    """Create a pull request manager instance."""
    return PullRequestManager(mock_repository, factory=mock_factory)

@pytest.mark.asyncio
async def test_get_pull_request(pull_request_manager: PullRequestManager, mock_repository: Mock, mock_pull_request: Mock) -> None:
    """Test getting a pull request."""
    mock_repository.get_pull.return_value = mock_pull_request
    
    # Get pull request
    pr = await pull_request_manager.get_pull_request(1)
    assert pr.number == 1
    assert pr.title == "Test PR"
    
    # Verify calls
    mock_repository.get_pull.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_create_pull_request(pull_request_manager: PullRequestManager, mock_repository: Mock, mock_pull_request: Mock) -> None:
    """Test creating a pull request."""
    # Set up mock pull request
    mock_pull_request.number = 1
    mock_pull_request.title = "Test PR"
    mock_pull_request.body = "Test Body"
    mock_pull_request.head = Mock()
    mock_pull_request.head.ref = "feature"
    mock_pull_request.base = Mock()
    mock_pull_request.base.ref = "main"
    mock_pull_request.draft = False
    mock_pull_request.maintainer_can_modify = True
    
    # Make create_pull awaitable
    async def async_create_pull(*args, **kwargs):
        return mock_pull_request
    mock_repository.create_pull = AsyncMock(side_effect=async_create_pull)
    
    # Create pull request
    config = PullRequestConfig(
        title="Test PR",
        body="Test Body",
        head="feature",
        base="main",
        draft=False,
        maintainer_can_modify=True
    )
    
    pr = await pull_request_manager.create_pull_request(
        title=config.title,
        body=config.body,
        head=config.head,
        base=config.base,
        draft=config.draft,
        maintainer_can_modify=config.maintainer_can_modify
    )
    
    # Verify result
    assert isinstance(pr, dict)
    assert pr["title"] == mock_pull_request.title
    assert pr["body"] == mock_pull_request.body
    assert pr["head"]["ref"] == mock_pull_request.head.ref
    assert pr["base"]["ref"] == mock_pull_request.base.ref
    assert pr["draft"] == mock_pull_request.draft
    assert pr["maintainer_can_modify"] == mock_pull_request.maintainer_can_modify
    
    # Verify calls
    mock_repository.create_pull.assert_called_once_with(
        title="Test PR",
        body="Test Body",
        head="feature",
        base="main",
        draft=False,
        maintainer_can_modify=True
    )

@pytest.mark.asyncio
async def test_update_pull_request(pull_request_manager: PullRequestManager, mock_repository: Mock, mock_pull_request: Mock) -> None:
    """Test updating a pull request."""
    mock_repository.get_pull.return_value = mock_pull_request
    
    # Update pull request
    config = PullRequestConfig(
        title="Updated PR",
        body="Updated Body",
        base="develop",
        maintainer_can_modify=False
    )
    pr = await pull_request_manager.update_pull_request(1, config)
    
    # Verify calls
    mock_repository.get_pull.assert_called_once_with(1)
    mock_pull_request.edit.assert_any_call(title="Updated PR")
    mock_pull_request.edit.assert_any_call(body="Updated Body")
    mock_pull_request.edit.assert_any_call(base="develop")
    mock_pull_request.edit.assert_any_call(maintainer_can_modify=False)

@pytest.mark.asyncio
async def test_list_pull_requests(pull_request_manager: PullRequestManager, mock_repository: Mock, mock_pull_request: Mock) -> None:
    """Test listing pull requests."""
    mock_repository.get_pulls.return_value = [mock_pull_request]
    
    # List pull requests
    prs = await pull_request_manager.list_pull_requests(
        state="open",
        head="feature",
        base="main",
        sort="created",
        direction="desc"
    )
    
    # Verify results
    assert len(prs) == 1
    assert prs[0].number == 1
    assert prs[0].title == "Test PR"
    
    # Verify calls
    mock_repository.get_pulls.assert_called_once_with(
        state="open",
        head="feature",
        base="main",
        sort="created",
        direction="desc"
    )

@pytest.mark.asyncio
async def test_merge_pull_request(pull_request_manager: PullRequestManager, mock_repository: Mock, mock_pull_request: Mock) -> None:
    """Test merging a pull request."""
    mock_repository.get_pull.return_value = mock_pull_request
    mock_pull_request.merge.return_value = True
    
    # Merge pull request
    result = await pull_request_manager.merge_pull_request(
        1,
        commit_title="Merge PR",
        commit_message="Merging test PR",
        merge_method="squash"
    )
    
    # Verify result
    assert result is True
    
    # Verify calls
    mock_repository.get_pull.assert_called_once_with(1)
    mock_pull_request.merge.assert_called_once_with(
        commit_title="Merge PR",
        commit_message="Merging test PR",
        merge_method="squash"
    )

@pytest.mark.asyncio
async def test_create_review(pull_request_manager: PullRequestManager, mock_repository: Mock, mock_pull_request: Mock) -> None:
    """Test creating a review."""
    mock_review = Mock(spec=PullRequestReview)
    mock_pull_request.create_review.return_value = mock_review
    mock_repository.get_pull.return_value = mock_pull_request
    
    # Create review
    review = await pull_request_manager.create_review(
        1,
        body="LGTM",
        event="APPROVE",
        comments=[{"path": "file.py", "position": 1, "body": "Nice!"}]
    )
    
    # Verify calls
    mock_repository.get_pull.assert_called_once_with(1)
    mock_pull_request.create_review.assert_called_once_with(
        body="LGTM",
        event="APPROVE",
        comments=[{"path": "file.py", "position": 1, "body": "Nice!"}]
    )

@pytest.mark.asyncio
async def test_request_review(pull_request_manager: PullRequestManager, mock_repository: Mock, mock_pull_request: Mock) -> None:
    """Test requesting reviews."""
    mock_repository.get_pull.return_value = mock_pull_request
    
    # Request reviews
    await pull_request_manager.request_review(1, ["user1", "user2"])
    
    # Verify calls
    mock_repository.get_pull.assert_called_once_with(1)
    mock_pull_request.create_review_request.assert_called_once_with(reviewers=["user1", "user2"])

@pytest.mark.asyncio
async def test_remove_review_request(pull_request_manager: PullRequestManager, mock_repository: Mock, mock_pull_request: Mock) -> None:
    """Test removing review requests."""
    mock_repository.get_pull.return_value = mock_pull_request
    
    # Remove review requests
    await pull_request_manager.remove_review_request(1, ["user1", "user2"])
    
    # Verify calls
    mock_repository.get_pull.assert_called_once_with(1)
    mock_pull_request.delete_review_request.assert_called_once_with(reviewers=["user1", "user2"])

@pytest.mark.asyncio
async def test_update_branch(pull_request_manager: PullRequestManager, mock_repository: Mock, mock_pull_request: Mock) -> None:
    """Test updating a pull request branch."""
    mock_repository.get_pull.return_value = mock_pull_request
    mock_pull_request.update_branch.return_value = True
    
    # Update branch
    result = await pull_request_manager.update_branch(1)
    
    # Verify result
    assert result is True
    
    # Verify calls
    mock_repository.get_pull.assert_called_once_with(1)
    mock_pull_request.update_branch.assert_called_once()

@pytest.mark.asyncio
async def test_close_pull_request(pull_request_manager: PullRequestManager, mock_repository: Mock, mock_pull_request: Mock) -> None:
    """Test closing a pull request."""
    mock_repository.get_pull.return_value = mock_pull_request
    
    # Close pull request
    pr = await pull_request_manager.close_pull_request(1)
    
    # Verify calls
    mock_repository.get_pull.assert_called_once_with(1)
    mock_pull_request.edit.assert_called_once_with(state="closed")

@pytest.mark.asyncio
async def test_reopen_pull_request(pull_request_manager: PullRequestManager, mock_repository: Mock, mock_pull_request: Mock) -> None:
    """Test reopening a pull request."""
    mock_repository.get_pull.return_value = mock_pull_request
    
    # Reopen pull request
    pr = await pull_request_manager.reopen_pull_request(1)
    
    # Verify calls
    mock_repository.get_pull.assert_called_once_with(1)
    mock_pull_request.edit.assert_called_once_with(state="open") 