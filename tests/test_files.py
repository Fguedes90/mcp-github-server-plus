"""Tests for the files module."""

import pytest
from unittest.mock import Mock, patch, PropertyMock
from base64 import b64encode
from github.ContentFile import ContentFile
from github.GitTree import GitTree
from github.GithubObject import NotSet
from mcp_github_server_plus.files.files import FileManager, FileContent

@pytest.fixture
def mock_repository() -> Mock:
    """Create a mock repository."""
    return Mock()

@pytest.fixture
def mock_content_file() -> Mock:
    """Create a mock content file."""
    content = "test content"
    encoded_content = b64encode(content.encode("utf-8")).decode("utf-8")
    
    mock = Mock(spec=ContentFile)
    mock.path = "test.txt"
    mock.content = encoded_content
    mock.sha = "test-sha"
    mock.encoding = "utf-8"
    mock.size = len(content)
    mock.type = "file"
    return mock

@pytest.fixture
def mock_git_tree() -> Mock:
    """Create a mock git tree."""
    return Mock(spec=GitTree)

@pytest.mark.asyncio
async def test_get_file(
    mock_repository: Mock,
    mock_content_file: Mock,
) -> None:
    """Test getting a file."""
    mock_repository.get_contents.return_value = mock_content_file
    
    manager = FileManager(mock_repository)
    file_content = await manager.get_file("test.txt")
    
    assert isinstance(file_content, FileContent)
    assert file_content.path == "test.txt"
    assert file_content.content == "test content"
    assert file_content.sha == "test-sha"
    assert file_content.encoding == "utf-8"
    assert file_content.size == len("test content")
    assert file_content.type == "file"
    
    # Test with ref
    file_content = await manager.get_file("test.txt", ref="main")
    mock_repository.get_contents.assert_called_with("test.txt", ref="main")

@pytest.mark.asyncio
async def test_get_file_directory_error(
    mock_repository: Mock,
) -> None:
    """Test error when getting a directory as file."""
    mock_repository.get_contents.return_value = []
    
    manager = FileManager(mock_repository)
    with pytest.raises(ValueError, match="Path 'test' is a directory"):
        await manager.get_file("test")

@pytest.mark.asyncio
async def test_get_file_no_encoding(
    mock_repository: Mock,
    mock_content_file: Mock,
) -> None:
    """Test getting a file without encoding specified."""
    mock_content_file.encoding = None
    mock_repository.get_contents.return_value = mock_content_file
    
    manager = FileManager(mock_repository)
    file_content = await manager.get_file("test.txt")
    assert file_content.encoding == "utf-8"  # Default encoding

@pytest.mark.asyncio
async def test_create_file(
    mock_repository: Mock,
    mock_content_file: Mock,
    mock_git_tree: Mock,
) -> None:
    """Test creating a file."""
    mock_repository.create_file.return_value = (mock_content_file, mock_git_tree)
    
    manager = FileManager(mock_repository)
    content_file, git_tree = await manager.create_file(
        path="test.txt",
        content="test content",
        message="Create test.txt",
    )
    
    assert content_file == mock_content_file
    assert git_tree == mock_git_tree
    mock_repository.create_file.assert_called_once()
    
    # Test with optional parameters
    await manager.create_file(
        path="test.txt",
        content="test content",
        message="Create test.txt",
        branch="main",
        committer={"name": "Test User", "email": "test@example.com"},
        author={"name": "Author", "email": "author@example.com"},
    )

@pytest.mark.asyncio
async def test_update_file(
    mock_repository: Mock,
    mock_content_file: Mock,
    mock_git_tree: Mock,
) -> None:
    """Test updating a file."""
    mock_repository.update_file.return_value = (mock_content_file, mock_git_tree)
    
    manager = FileManager(mock_repository)
    content_file, git_tree = await manager.update_file(
        path="test.txt",
        content="updated content",
        message="Update test.txt",
        sha="test-sha",
    )
    
    assert content_file == mock_content_file
    assert git_tree == mock_git_tree
    mock_repository.update_file.assert_called_once()
    
    # Test with optional parameters
    await manager.update_file(
        path="test.txt",
        content="updated content",
        message="Update test.txt",
        sha="test-sha",
        branch="main",
        committer={"name": "Test User", "email": "test@example.com"},
        author={"name": "Author", "email": "author@example.com"},
    )

@pytest.mark.asyncio
async def test_delete_file(
    mock_repository: Mock,
) -> None:
    """Test deleting a file."""
    mock_repository.delete_file.return_value = {"commit": {"sha": "delete-sha"}}
    
    manager = FileManager(mock_repository)
    result = await manager.delete_file(
        path="test.txt",
        message="Delete test.txt",
        sha="test-sha",
    )
    
    assert result == {"commit": {"sha": "delete-sha"}}
    mock_repository.delete_file.assert_called_once()
    
    # Test with optional parameters
    await manager.delete_file(
        path="test.txt",
        message="Delete test.txt",
        sha="test-sha",
        branch="main",
        committer={"name": "Test User", "email": "test@example.com"},
        author={"name": "Author", "email": "author@example.com"},
    )

@pytest.mark.asyncio
async def test_get_tree(
    mock_repository: Mock,
    mock_content_file: Mock,
) -> None:
    """Test getting a file tree."""
    mock_repository.get_contents.return_value = [mock_content_file]
    
    manager = FileManager(mock_repository)
    tree = await manager.get_tree()
    assert tree == [mock_content_file]
    mock_repository.get_contents.assert_called_with("", ref=None)
    
    # Test with path and ref
    tree = await manager.get_tree(path="src", recursive=True, ref="main")
    mock_repository.get_contents.assert_called_with("src", ref="main")

@pytest.mark.asyncio
async def test_get_file_with_different_encoding(
    mock_repository: Mock,
    mock_content_file: Mock,
) -> None:
    """Test getting a file with a different encoding."""
    content = "test content"
    encoded_content = b64encode(content.encode("latin1")).decode("utf-8")
    mock_content_file.content = encoded_content
    mock_content_file.encoding = "latin1"
    mock_repository.get_contents.return_value = mock_content_file
    
    manager = FileManager(mock_repository)
    file_content = await manager.get_file("test.txt")
    assert file_content.encoding == "latin1"
    assert file_content.content == content

@pytest.mark.asyncio
async def test_create_file_with_unicode(
    mock_repository: Mock,
    mock_content_file: Mock,
    mock_git_tree: Mock,
) -> None:
    """Test creating a file with Unicode content."""
    mock_repository.create_file.return_value = (mock_content_file, mock_git_tree)
    
    manager = FileManager(mock_repository)
    content = "Hello, 世界! 🌍"
    await manager.create_file(
        path="test.txt",
        content=content,
        message="Create test.txt with Unicode",
    )
    
    # Verify the content was properly encoded
    expected_content = b64encode(content.encode("utf-8")).decode("utf-8")
    mock_repository.create_file.assert_called_with(
        path="test.txt",
        message="Create test.txt with Unicode",
        content=expected_content,
        branch=NotSet,
        committer=NotSet,
        author=NotSet,
    ) 