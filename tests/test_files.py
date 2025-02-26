"""Tests for the files module."""

import pytest
from unittest.mock import Mock, patch, call, MagicMock
from pathlib import Path
from github.Repository import Repository as GithubRepository
from github.ContentFile import ContentFile
from github.GithubObject import NotSet
from mcp_pygithub.operations.files import FileManager, FileConfig, GetFileContentsConfig, FileContent, CreateOrUpdateFileConfig, PushFilesContentConfig, PushFilesFromPathConfig, FilePath
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
    repo = Mock(spec=GithubRepository)
    repo.owner = Mock()
    repo.owner.login = "test-owner"
    repo.name = "test-repo"
    repo.default_branch = "main"
    return repo

@pytest.fixture
def mock_content_file(mock_repository: Mock) -> Mock:
    """Create a mock content file."""
    content_file = Mock(spec=ContentFile)
    content_file.path = "test.txt"
    content_file.decoded_content = b"test content"
    content_file.content = "test content"
    content_file.sha = "test-sha"
    content_file.encoding = "utf-8"
    content_file.size = 12
    content_file.type = "file"
    content_file.url = "https://api.github.com/repos/test/test/contents/test.txt"
    content_file.html_url = "https://github.com/test/test/blob/main/test.txt"
    content_file.git_url = "https://api.github.com/repos/test/test/git/blobs/test-sha"
    content_file.download_url = "https://raw.githubusercontent.com/test/test/main/test.txt"
    return content_file

@pytest.fixture
def file_manager(mock_repository: Mock, mock_factory: GitHubClientFactory) -> FileManager:
    """Create a file manager instance."""
    return FileManager(mock_repository, factory=mock_factory)

@pytest.mark.asyncio
async def test_get_file_contents(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test getting file contents."""
    mock_repository.get_contents.return_value = mock_content_file
    
    # Get file contents
    config = GetFileContentsConfig(path="test.txt", branch="main")
    content = await file_manager.get_file_contents(config)
    assert content.path == "test.txt"
    assert content.content == "test content"
    
    # Verify calls
    mock_repository.get_contents.assert_called_once_with("test.txt", ref="main")

@pytest.mark.asyncio
async def test_create_file(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test creating a file."""
    mock_repository.create_file.return_value = (mock_content_file, None)
    
    # Create file
    config = CreateOrUpdateFileConfig(
        path="test.txt",
        content="test content",
        message="Create test file",
        branch="main"
    )
    result = await file_manager.create_or_update_file(config)
    
    # Verify result
    assert result["content"] == mock_content_file
    
    # Verify calls
    mock_repository.create_file.assert_called_once_with(
        path="test.txt",
        message="Create test file",
        content=b"test content",
        branch="main"
    )

@pytest.mark.asyncio
async def test_update_file(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test updating a file."""
    mock_repository.update_file.return_value = (mock_content_file, None)
    
    # Update file
    config = CreateOrUpdateFileConfig(
        path="test.txt",
        content="updated content",
        message="Update test file",
        branch="main",
        sha="test-sha"
    )
    result = await file_manager.create_or_update_file(config)
    
    # Verify result
    assert result["content"] == mock_content_file
    
    # Verify calls
    mock_repository.update_file.assert_called_once_with(
        path="test.txt",
        message="Update test file",
        content=b"updated content",
        sha="test-sha",
        branch="main"
    )

@pytest.mark.asyncio
async def test_delete_file(file_manager: FileManager, mock_repository: Mock) -> None:
    """Test deleting a file."""
    mock_repository.delete_file.return_value = (None, None)
    
    # Delete file
    config = FileConfig(
        path="test.txt",
        message="Delete test file",
        branch="main",
        sha="test-sha"
    )
    result = await file_manager.delete_file(config)
    
    # Verify result
    assert "commit" in result
    
    # Verify calls
    mock_repository.delete_file.assert_called_once_with(
        path="test.txt",
        message="Delete test file",
        sha="test-sha",
        branch="main"
    )

@pytest.mark.asyncio
async def test_get_directory_contents(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test getting directory contents."""
    mock_repository.get_contents.return_value = [mock_content_file]
    
    # Get directory contents
    config = GetFileContentsConfig(path="test-dir/", branch="main")
    contents = await file_manager.get_file_contents(config)
    assert isinstance(contents, list)
    assert len(contents) == 1
    assert contents[0].path == "test.txt"
    
    # Verify calls
    mock_repository.get_contents.assert_called_once_with("test-dir/", ref="main")

@pytest.mark.asyncio
async def test_create_directory(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test creating a directory."""
    mock_repository.create_file.return_value = (mock_content_file, None)
    
    # Create directory
    config = FileConfig(
        path="test-dir",
        message="Create test directory"
    )
    result = await file_manager.create_directory(config)
    
    # Verify result
    assert result["content"] == mock_content_file
    
    # Verify calls
    mock_repository.create_file.assert_called_once_with(
        path="test-dir/.gitkeep",
        message="Create test directory",
        content=b"",
        branch=NotSet
    )

@pytest.mark.asyncio
async def test_push_files(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test pushing multiple files."""
    # Mock commit object
    mock_commit = Mock()
    mock_commit.sha = "test-commit-sha"
    mock_commit.message = "Push multiple files"
    mock_commit.tree.sha = "test-tree-sha"
    mock_commit.parents = []  # Empty list of parents
    
    # Mock git ref
    mock_git_ref = Mock()
    mock_git_ref.ref = "refs/heads/main"
    mock_git_ref.object.sha = "test-ref-sha"
    
    # Mock repository methods
    mock_repository.create_file.return_value = (mock_content_file, None)
    mock_repository.update_file.return_value = (mock_content_file, None)
    mock_repository.create_git_commit.return_value = mock_commit
    mock_repository.get_git_ref.return_value = mock_git_ref
    
    # Push files
    files = [
        FileContent(
            path="new.txt",
            content="new content"
        ),
        FileContent(
            path="existing.txt",
            content="updated content",
            sha="test-sha"
        )
    ]
    
    config = PushFilesContentConfig(
        branch="main",
        files=files,
        message="Push multiple files"
    )
    
    results = await file_manager.push_files_content(config)
    
    # Verify results
    assert results["ref"] == "refs/heads/main"
    assert results["object"]["sha"] == "test-ref-sha"
    
    # Verify calls
    assert mock_repository.get_git_ref.call_count == 2
    assert mock_repository.get_git_ref.call_args_list == [
        call("heads/main"),
        call("heads/main")
    ]
    mock_repository.create_git_tree.assert_called_once()
    mock_repository.create_git_commit.assert_called_once_with(
        message="Push multiple files",
        tree=mock_repository.create_git_tree.return_value.sha,
        parents=["test-ref-sha"]
    )

@pytest.mark.asyncio
async def test_push_directory(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock, tmp_path: Path) -> None:
    """Test pushing a directory."""
    # Create test files
    test_dir = tmp_path / "test-dir"
    test_dir.mkdir()
    test_file = test_dir / "test.txt"
    test_file.write_text("test content")
    
    # Mock commit object
    mock_commit = Mock()
    mock_commit.sha = "test-commit-sha"
    mock_commit.message = "Push test directory"
    mock_commit.tree.sha = "test-tree-sha"
    mock_commit.parents = []  # Empty list of parents
    
    # Mock git ref
    mock_git_ref = Mock()
    mock_git_ref.ref = "refs/heads/main"
    mock_git_ref.object.sha = "test-ref-sha"
    
    # Mock repository methods
    mock_repository.create_file.return_value = (mock_content_file, None)
    mock_repository.create_git_commit.return_value = mock_commit
    mock_repository.get_git_ref.return_value = mock_git_ref
    
    # Push directory
    config = PushFilesFromPathConfig(
        branch="main",
        message="Push test directory",
        files=[
            FilePath(
                path="remote-dir/test.txt",
                filepath=str(test_file)
            )
        ]
    )
    
    results = await file_manager.push_files_from_path(config)
    
    # Verify results
    assert results["ref"] == "refs/heads/main"
    assert results["object"]["sha"] == "test-ref-sha"
    
    # Verify calls
    assert mock_repository.get_git_ref.call_count == 2
    assert mock_repository.get_git_ref.call_args_list == [
        call("heads/main"),
        call("heads/main")
    ]
    mock_repository.create_git_tree.assert_called_once()
    mock_repository.create_git_commit.assert_called_once_with(
        message="Push test directory",
        tree=mock_repository.create_git_tree.return_value.sha,
        parents=["test-ref-sha"]
    )

# New tests to cover the missing lines

@pytest.mark.asyncio
async def test_get_file_contents_directory_not_expected(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test getting file contents when a directory is returned but not expected."""
    # Mock a list of content files to simulate getting a directory
    mock_repository.get_contents.return_value = [mock_content_file]
    
    # Get file contents for a path not ending with '/'
    config = GetFileContentsConfig(path="test-dir", branch="main")
    
    # This should raise ValueError because we got a directory but didn't expect one
    with pytest.raises(ValueError, match="Path 'test-dir' is a directory"):
        await file_manager.get_file_contents(config)
    
    # Verify call
    mock_repository.get_contents.assert_called_once_with("test-dir", ref="main")

@pytest.mark.asyncio
async def test_push_files_from_path_file_not_found(file_manager: FileManager, mock_repository: Mock, tmp_path: Path) -> None:
    """Test pushing files from path with a non-existent file."""
    # Create config with non-existent file
    config = PushFilesFromPathConfig(
        branch="main",
        message="Push non-existent file",
        files=[
            FilePath(
                path="remote-dir/non-existent.txt",
                filepath=str(tmp_path / "non-existent.txt")
            )
        ]
    )
    
    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        await file_manager.push_files_from_path(config)

@pytest.mark.asyncio
async def test_create_file_with_direct_method(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test create_file method directly."""
    # Mock repository methods
    mock_repository.get_contents.side_effect = Exception("File not found")
    mock_repository.create_file.return_value = (mock_content_file, mock_content_file)
    
    # Call create_file method directly
    content, commit = await file_manager.create_file(
        path="new-file.txt",
        content="new content",
        message="Create new file",
        branch="main"
    )
    
    # Verify result
    assert content == mock_content_file
    assert commit == mock_content_file
    
    # Verify repository method was called
    mock_repository.create_file.assert_called_once()

@pytest.mark.asyncio
async def test_create_file_with_existing_file(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test create_file method when file already exists."""
    # Mock repository methods
    mock_repository.get_contents.return_value = mock_content_file
    mock_repository.update_file.return_value = (mock_content_file, mock_content_file)
    
    # Call create_file method
    content, commit = await file_manager.create_file(
        path="existing-file.txt",
        content="updated content",
        message="Update existing file",
        branch="main"
    )
    
    # Verify result
    assert content == mock_content_file
    assert commit == mock_content_file
    
    # Verify repository methods were called
    mock_repository.get_contents.assert_called_once()
    mock_repository.update_file.assert_called_once()

@pytest.mark.asyncio
async def test_create_file_with_dict_response(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test create_file method with dictionary response."""
    # Mock repository methods to return a dictionary
    dict_response = {'content': mock_content_file, 'commit': mock_content_file}
    mock_repository.get_contents.side_effect = Exception("File not found")
    mock_repository.create_file.return_value = dict_response
    
    # Call create_file method
    content, commit = await file_manager.create_file(
        path="new-file.txt",
        content="new content",
        message="Create new file",
        branch="main"
    )
    
    # Verify result
    assert content == mock_content_file
    assert commit == mock_content_file

@pytest.mark.asyncio
async def test_create_file_unexpected_response(file_manager: FileManager, mock_repository: Mock) -> None:
    """Test create_file method with unexpected response type."""
    # Mock repository methods
    mock_repository.get_contents.side_effect = Exception("File not found")
    # Return an integer which is neither a tuple nor a dict
    mock_repository.create_file.return_value = 42
    
    # Call create_file method, should raise ValueError
    with pytest.raises(ValueError):
        await file_manager.create_file(
            path="new-file.txt",
            content="new content",
            message="Create new file",
            branch="main"
        )

@pytest.mark.asyncio
async def test_update_file_direct_method(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test update_file method directly."""
    # Mock repository methods
    mock_repository.update_file.return_value = (mock_content_file, mock_content_file)
    
    # Call update_file method
    content, commit = await file_manager.update_file(
        path="existing-file.txt",
        content="updated content",
        message="Update file",
        sha="test-sha",
        branch="main"
    )
    
    # Verify result
    assert content == mock_content_file
    assert commit == mock_content_file
    
    # Verify repository method was called with expected args
    mock_repository.update_file.assert_called_once_with(
        path="existing-file.txt",
        message="Update file",
        content="dXBkYXRlZCBjb250ZW50",  # base64 encoded "updated content"
        sha="test-sha",
        branch="main",
        committer=NotSet,
        author=NotSet
    )

@pytest.mark.asyncio
async def test_get_tree_method(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test get_tree method."""
    # Mock repository methods
    mock_repository.get_contents.return_value = [mock_content_file]
    
    # Call get_tree method
    result = await file_manager.get_tree(path="test-dir", ref="main")
    
    # Verify result
    assert result == [mock_content_file]
    
    # Verify repository method was called
    mock_repository.get_contents.assert_called_once_with("test-dir", ref="main")

@pytest.mark.asyncio
async def test_get_file_method(file_manager: FileManager, mock_repository: Mock, mock_content_file: Mock) -> None:
    """Test get_file method."""
    # Mock repository methods
    mock_repository.get_contents.return_value = mock_content_file
    
    # Call get_file method
    result = await file_manager.get_file(path="test.txt", ref="main")
    
    # Verify result is a FileContent object with expected attributes
    assert isinstance(result, FileContent)
    assert result.path == "test.txt"
    assert result.content == "test content"
    
    # Verify repository method was called
    mock_repository.get_contents.assert_called_once_with("test.txt", ref="main") 