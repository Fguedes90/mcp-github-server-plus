"""Tests for the search module."""

import pytest
from unittest.mock import Mock, patch, PropertyMock
from github.Repository import Repository as GithubRepository
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.ContentFile import ContentFile
from github.Commit import Commit
from mcp_pygithub.operations.search import SearchManager, SearchConfig
from mcp_pygithub.operations.files import FileContent

@pytest.fixture
def mock_repository() -> Mock:
    """Create a mock repository."""
    mock = Mock(spec=GithubRepository)
    type(mock).full_name = PropertyMock(return_value="test-owner/test-repo")
    return mock

@pytest.fixture
def mock_issue() -> Mock:
    """Create a mock issue."""
    mock = Mock(spec=Issue)
    mock.number = 1
    mock.title = "Test Issue"
    mock.body = "Test Body"
    mock.state = "open"
    return mock

@pytest.fixture
def mock_pull_request() -> Mock:
    """Create a mock pull request."""
    mock = Mock(spec=PullRequest)
    mock.number = 1
    mock.title = "Test PR"
    mock.body = "Test Body"
    mock.state = "open"
    return mock

@pytest.fixture
def mock_content_file() -> Mock:
    """Create a mock content file."""
    mock = Mock(spec=ContentFile)
    mock.path = "test.txt"
    mock.content = "test content"
    mock.sha = "test-sha"
    mock.type = "file"
    return mock

@pytest.fixture
def mock_commit() -> Mock:
    """Create a mock commit."""
    mock = Mock(spec=Commit)
    mock.sha = "test-sha"
    mock.commit.message = "Test commit"
    return mock

@pytest.fixture
def search_manager(mock_repository: Mock) -> SearchManager:
    """Create a search manager instance."""
    return SearchManager(mock_repository)

@pytest.mark.asyncio
async def test_search_issues_basic(search_manager: SearchManager, mock_repository: Mock, mock_issue: Mock) -> None:
    """Test basic issue search."""
    mock_repository.get_issues.return_value = [mock_issue]
    
    # Search issues
    config = SearchConfig(query="test")
    issues = await search_manager.search_issues(config)
    
    # Verify results
    assert len(issues) == 1
    assert issues[0].number == 1
    assert issues[0].title == "Test Issue"
    
    # Verify calls
    mock_repository.get_issues.assert_called_once_with(
        sort=None,
        direction="desc",
        per_page=30,
        page=1,
    )

@pytest.mark.asyncio
async def test_search_issues_with_filters(search_manager: SearchManager, mock_repository: Mock, mock_issue: Mock) -> None:
    """Test issue search with filters."""
    mock_repository.get_issues.return_value = [mock_issue]
    
    # Search issues with filters
    config = SearchConfig(
        query="test",
        sort="created",
        order="asc",
        per_page=10,
        page=2
    )
    issues = await search_manager.search_issues(config)
    
    # Verify results
    assert len(issues) == 1
    assert issues[0].number == 1
    assert issues[0].title == "Test Issue"
    
    # Verify calls
    mock_repository.get_issues.assert_called_once_with(
        sort="created",
        direction="asc",
        per_page=10,
        page=2,
    )

@pytest.mark.asyncio
async def test_search_pulls_basic(search_manager: SearchManager, mock_repository: Mock, mock_pull_request: Mock) -> None:
    """Test basic pull request search."""
    mock_repository.get_pulls.return_value = [mock_pull_request]
    
    # Search pull requests
    config = SearchConfig(query="test")
    pulls = await search_manager.search_pulls(config)
    
    # Verify results
    assert len(pulls) == 1
    assert pulls[0].number == 1
    assert pulls[0].title == "Test PR"
    
    # Verify calls
    mock_repository.get_pulls.assert_called_once_with(
        sort=None,
        direction="desc",
        per_page=30,
        page=1,
    )

@pytest.mark.asyncio
async def test_search_pulls_with_filters(search_manager: SearchManager, mock_repository: Mock, mock_pull_request: Mock) -> None:
    """Test pull request search with filters."""
    mock_repository.get_pulls.return_value = [mock_pull_request]
    
    # Search pull requests with filters
    config = SearchConfig(
        query="test",
        sort="updated",
        order="asc",
        per_page=10,
        page=2
    )
    pulls = await search_manager.search_pulls(config)
    
    # Verify results
    assert len(pulls) == 1
    assert pulls[0].number == 1
    assert pulls[0].title == "Test PR"
    
    # Verify calls
    mock_repository.get_pulls.assert_called_once_with(
        sort="updated",
        direction="asc",
        per_page=10,
        page=2,
    )

@pytest.mark.asyncio
async def test_search_code_basic(search_manager: SearchManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test basic code search."""
    # Set up mock content file
    mock_content_file.path = "test.txt"
    mock_content_file.decoded_content = b"test content"
    mock_content_file.sha = "test-sha"
    mock_content_file.encoding = "utf-8"
    mock_content_file.size = 12
    mock_content_file.type = "file"
    mock_content_file.url = "url1"
    mock_content_file.html_url = "html1"
    mock_content_file.git_url = "git1"
    mock_content_file.download_url = "download1"
    
    mock_repository.get_contents = Mock(return_value=[mock_content_file])
    
    # Search code
    config = SearchConfig(query="test")
    results = await search_manager.search_code(config)
    
    # Verify results
    assert len(results) == 1
    result = results[0]
    assert isinstance(result, dict)
    assert result["path"] == "test.txt"
    assert result["content"] == "test content"
    assert result["sha"] == "test-sha"
    assert result["encoding"] == "utf-8"
    assert result["size"] == 12
    assert result["type"] == "file"
    assert result["url"] == "url1"
    assert result["html_url"] == "html1"
    assert result["git_url"] == "git1"
    assert result["download_url"] == "download1"
    
    # Verify calls
    mock_repository.get_contents.assert_called_once_with("")

@pytest.mark.asyncio
async def test_search_commits_basic(search_manager: SearchManager, mock_repository: Mock, mock_commit: Mock) -> None:
    """Test basic commit search."""
    mock_repository.get_commits.return_value = [mock_commit]
    
    # Search commits
    config = SearchConfig(query="test")
    commits = await search_manager.search_commits(config)
    
    # Verify results
    assert len(commits) == 1
    assert commits[0] == "test-sha"
    
    # Verify calls
    mock_repository.get_commits.assert_called_once_with(
        sha=None,
        path=None,
        since=None,
        until=None,
        author=None,
        per_page=30,
        page=1,
    )

@pytest.mark.asyncio
async def test_search_commits_with_filters(search_manager: SearchManager, mock_repository: Mock, mock_commit: Mock) -> None:
    """Test commit search with filters."""
    mock_repository.get_commits.return_value = [mock_commit]
    
    # Search commits with filters
    config = SearchConfig(
        query="test",
        sort="author-date",
        order="asc",
        per_page=10,
        page=2
    )
    commits = await search_manager.search_commits(config)
    
    # Verify results
    assert len(commits) == 1
    assert commits[0] == "test-sha"
    
    # Verify calls
    mock_repository.get_commits.assert_called_once_with(
        sha=None,
        path=None,
        since=None,
        until=None,
        author=None,
        per_page=10,
        page=2,
    )

@pytest.mark.asyncio
async def test_search_code_error_handling(search_manager: SearchManager, mock_repository: Mock) -> None:
    """Test error handling in code search."""
    # Setup mock to raise an exception
    mock_repository.get_contents.side_effect = Exception("Test error")
    
    # Search code with error
    config = SearchConfig(query="test")
    
    # Verify error handling
    from mcp_pygithub.common.errors import SearchError
    with pytest.raises(SearchError, match="Failed to search code: Test error"):
        await search_manager.search_code(config)
    
    # Verify calls
    mock_repository.get_contents.assert_called_once_with("")

@pytest.mark.asyncio
async def test_search_code_with_filters(search_manager: SearchManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test code search with path and extension filters."""
    # Set up mock content files
    txt_file = Mock(spec=ContentFile)
    txt_file.path = "docs/readme.txt"
    txt_file.decoded_content = b"text content"
    txt_file.sha = "txt-sha"
    txt_file.encoding = "utf-8"
    txt_file.size = 12
    txt_file.type = "file"
    txt_file.url = "url-txt"
    txt_file.html_url = "html-txt"
    txt_file.git_url = "git-txt"
    txt_file.download_url = "download-txt"
    
    py_file = Mock(spec=ContentFile)
    py_file.path = "src/main.py"
    py_file.decoded_content = b"python content"
    py_file.sha = "py-sha"
    py_file.encoding = "utf-8"
    py_file.size = 14
    py_file.type = "file"
    py_file.url = "url-py"
    py_file.html_url = "html-py"
    py_file.git_url = "git-py"
    py_file.download_url = "download-py"
    
    mock_repository.get_contents = Mock(return_value=[txt_file, py_file])
    
    # Search code with path filter
    config = SearchConfig(query="test", path="src", extension=None)
    results = await search_manager.search_code(config)
    
    # Verify results
    assert len(results) == 1
    assert results[0]["path"] == "src/main.py"
    
    # Search code with extension filter
    config = SearchConfig(query="test", path=None, extension=".txt")
    results = await search_manager.search_code(config)
    
    # Verify results
    assert len(results) == 1
    assert results[0]["path"] == "docs/readme.txt"
    
    # Verify calls
    assert mock_repository.get_contents.call_count == 2

@pytest.mark.asyncio
async def test_search_commits_config_validation(search_manager: SearchManager, mock_repository: Mock, mock_commit: Mock) -> None:
    """Test config validation and query building in search_commits."""
    mock_repository.get_commits.return_value = [mock_commit]
    
    # Create a custom config object that's not a SearchConfig
    class CustomConfig:
        def __init__(self):
            self.query = "test-query"
            self.per_page = 5
            self.page = 2
            self.__dict__ = {"query": self.query, "per_page": self.per_page, "page": self.page}
    
    custom_config = CustomConfig()
    
    # Search commits with custom config
    commits = await search_manager.search_commits(custom_config)
    
    # Verify results
    assert len(commits) == 1
    assert commits[0] == "test-sha"
    
    # Verify the config was properly validated and used
    mock_repository.get_commits.assert_called_once_with(
        sha=None,
        path=None,
        since=None,
        until=None,
        author=None,
        per_page=5,
        page=2,
    )

@pytest.mark.asyncio
async def test_search_code_single_content(search_manager: SearchManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test code search when get_contents returns a single file instead of a list."""
    # Set up mock content file
    mock_content_file.path = "README.md"
    mock_content_file.decoded_content = b"# Readme"
    mock_content_file.sha = "readme-sha"
    mock_content_file.encoding = "utf-8"
    mock_content_file.size = 8
    mock_content_file.type = "file"
    mock_content_file.url = "url-readme"
    mock_content_file.html_url = "html-readme"
    mock_content_file.git_url = "git-readme"
    mock_content_file.download_url = "download-readme"
    
    # Return a single ContentFile object, not a list
    mock_repository.get_contents.return_value = mock_content_file
    
    # Search code
    config = SearchConfig(query="test")
    results = await search_manager.search_code(config)
    
    # Verify results
    assert len(results) == 1
    assert results[0]["path"] == "README.md"
    assert results[0]["content"] == "# Readme"
    
    # Verify calls
    mock_repository.get_contents.assert_called_once_with("") 