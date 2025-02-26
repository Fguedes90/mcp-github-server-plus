"""Additional tests for the files module to increase test coverage."""

import os
import pytest
from unittest.mock import Mock, patch, AsyncMock
from base64 import b64encode
from github.Repository import Repository as GithubRepository
from github.ContentFile import ContentFile
from github.GitTree import GitTree
from github.GithubObject import NotSet
from mcp_pygithub.operations.files import (
    FileManager, 
    FileContent, 
    CreateOrUpdateFileConfig, 
    GetFileContentsConfig, 
    PushFilesContentConfig, 
    PushFilesFromPathConfig,
    FilePath
)

@pytest.fixture
def mock_repository() -> Mock:
    """Create a mock repository."""
    return Mock(spec=GithubRepository)

@pytest.fixture
def file_manager(mock_repository: Mock) -> FileManager:
    """Create a FileManager instance."""
    return FileManager(mock_repository)

@pytest.mark.asyncio
async def test_create_or_update_file(
    mock_repository: Mock,
    file_manager: FileManager
) -> None:
    """Test creating or updating a file with various configurations."""
    # Mock the repository's create_file and update_file methods
    mock_content_file = Mock(spec=ContentFile)
    mock_commit = Mock()
    mock_repository.create_file.return_value = (mock_content_file, mock_commit)
    mock_repository.update_file.return_value = (mock_content_file, mock_commit)

    # Test creating a file
    create_config = CreateOrUpdateFileConfig(
        path="test.txt",
        content="Test content",
        message="Create test file",
        branch="main"
    )
    result = await file_manager.create_or_update_file(create_config)
    assert result["content"] == mock_content_file
    assert result["commit"] == mock_commit
    mock_repository.create_file.assert_called_once()

    # Test updating a file
    update_config = CreateOrUpdateFileConfig(
        path="test.txt",
        content="Updated content",
        message="Update test file",
        branch="main",
        sha="old-sha"
    )
    result = await file_manager.create_or_update_file(update_config)
    assert result["content"] == mock_content_file
    assert result["commit"] == mock_commit
    mock_repository.update_file.assert_called_once()

@pytest.mark.asyncio
async def test_create_tree(
    mock_repository: Mock,
    file_manager: FileManager
) -> None:
    """Test creating a Git tree."""
    # Prepare test files
    files = [
        FileContent(path="file1.txt", content="Content 1"),
        FileContent(path="file2.txt", content="Content 2")
    ]

    # Mock the repository's create_git_tree method
    mock_tree = Mock(spec=GitTree)
    mock_repository.create_git_tree.return_value = mock_tree

    # Test creating tree with no base tree
    result = await file_manager.create_tree(files)
    assert result == mock_tree
    mock_repository.create_git_tree.assert_called_once_with(
        [
            {"path": "file1.txt", "mode": "100644", "type": "blob", "content": "Content 1"},
            {"path": "file2.txt", "mode": "100644", "type": "blob", "content": "Content 2"}
        ],
        base_tree=NotSet
    )

    # Test creating tree with base tree
    await file_manager.create_tree(files, base_tree="base-sha")
    mock_repository.create_git_tree.assert_called_with(
        [
            {"path": "file1.txt", "mode": "100644", "type": "blob", "content": "Content 1"},
            {"path": "file2.txt", "mode": "100644", "type": "blob", "content": "Content 2"}
        ],
        base_tree="base-sha"
    )

@pytest.mark.asyncio
async def test_create_commit(
    mock_repository: Mock,
    file_manager: FileManager
) -> None:
    """Test creating a Git commit."""
    # Mock the repository's create_git_commit method
    mock_commit = Mock()
    mock_commit.sha = "new-commit-sha"
    mock_commit.message = "Test commit"
    mock_commit.tree.sha = "tree-sha"
    mock_commit.parents = [Mock(sha="parent1-sha"), Mock(sha="parent2-sha")]
    mock_repository.create_git_commit.return_value = mock_commit

    # Test commit creation
    result = await file_manager.create_commit(
        "Test commit message", 
        "tree-sha", 
        ["parent1-sha", "parent2-sha"]
    )

    assert result == {
        "sha": "new-commit-sha",
        "message": "Test commit",
        "tree": {"sha": "tree-sha"},
        "parents": [{"sha": "parent1-sha"}, {"sha": "parent2-sha"}]
    }
    mock_repository.create_git_commit.assert_called_once_with(
        message="Test commit message",
        tree="tree-sha",
        parents=["parent1-sha", "parent2-sha"]
    )

@pytest.mark.asyncio
async def test_update_reference(
    mock_repository: Mock,
    file_manager: FileManager
) -> None:
    """Test updating a Git reference."""
    # Mock the repository's get_git_ref method
    mock_ref = Mock()
    mock_ref.ref = "refs/heads/main"
    mock_ref.object.sha = "new-sha"
    mock_repository.get_git_ref.return_value = mock_ref

    # Test reference update
    result = await file_manager.update_reference("heads/main", "new-sha")
    
    assert result == {
        "ref": "refs/heads/main",
        "object": {"sha": "new-sha"}
    }
    mock_ref.edit.assert_called_once_with(sha="new-sha", force=True)

@pytest.mark.asyncio
async def test_push_files_content(
    mock_repository: Mock,
    file_manager: FileManager
) -> None:
    """Test pushing multiple files content."""
    # Prepare test configuration
    config = PushFilesContentConfig(
        branch="main",
        files=[
            FileContent(path="file1.txt", content="Content 1"),
            FileContent(path="file2.txt", content="Content 2")
        ],
        message="Push multiple files"
    )

    # Mock the necessary methods
    mock_ref = Mock()
    mock_ref.object.sha = "base-commit-sha"
    mock_repository.get_git_ref.return_value = mock_ref

    mock_tree = Mock(spec=GitTree)
    mock_tree.sha = "new-tree-sha"
    file_manager.create_tree = AsyncMock(return_value=mock_tree)

    mock_commit = Mock()
    mock_commit.sha = "new-commit-sha"
    file_manager.create_commit = AsyncMock(return_value={
        "sha": "new-commit-sha",
        "message": "Push multiple files",
        "tree": {"sha": "new-tree-sha"},
        "parents": [{"sha": "base-commit-sha"}]
    })

    file_manager.update_reference = AsyncMock(return_value={
        "ref": "refs/heads/main",
        "object": {"sha": "new-commit-sha"}
    })

    # Test pushing files content
    result = await file_manager.push_files_content(config)

    # Verify method calls and result
    mock_repository.get_git_ref.assert_called_once_with("heads/main")
    file_manager.create_tree.assert_called_once()
    file_manager.create_commit.assert_called_once()
    file_manager.update_reference.assert_called_once()

    assert result == {
        "ref": "refs/heads/main",
        "object": {"sha": "new-commit-sha"}
    }

@pytest.mark.asyncio
async def test_push_files_from_path(
    mock_repository: Mock,
    file_manager: FileManager,
    tmp_path: str
) -> None:
    """Test pushing files from filesystem paths."""
    # Create temporary files
    file1_path = os.path.join(tmp_path, "file1.txt")
    file2_path = os.path.join(tmp_path, "file2.txt")
    
    with open(file1_path, "w") as f:
        f.write("Content 1")
    
    with open(file2_path, "w") as f:
        f.write("Content 2")

    # Prepare test configuration
    config = PushFilesFromPathConfig(
        branch="main",
        files=[
            FilePath(path="file1.txt", filepath=file1_path),
            FilePath(path="file2.txt", filepath=file2_path)
        ],
        message="Push files from path"
    )

    # Mock the push_files_content method
    file_manager.push_files_content = AsyncMock(return_value={
        "ref": "refs/heads/main",
        "object": {"sha": "new-commit-sha"}
    })

    # Test pushing files from path
    result = await file_manager.push_files_from_path(config)
    
    assert result == {
        "ref": "refs/heads/main",
        "object": {"sha": "new-commit-sha"}
    }

@pytest.mark.asyncio
async def test_get_file_contents_error_handling(
    mock_repository: Mock,
    file_manager: FileManager
) -> None:
    """Test error handling in get_file_contents method."""
    # Prepare test configuration
    config = GetFileContentsConfig(
        path="test.txt",
        branch="main"
    )

    # Test handling of non-existent file
    mock_repository.get_contents.side_effect = Exception("File not found")
    
    with pytest.raises(Exception, match="File not found"):
        await file_manager.get_file_contents(config)

    # Reset mock for next test
    mock_repository.get_contents.side_effect = None
    mock_repository.get_contents.reset_mock()

    # Test with a directory that ends with /
    config.path = "test/"
    mock_content_files = [
        Mock(spec=ContentFile, path="test/file1.txt", name="file1.txt",
             decoded_content=b"content1",
             encoding="utf-8", sha="sha1", size=8, type="file",
             url="url1", html_url="html1", git_url="git1", download_url="download1"),
        Mock(spec=ContentFile, path="test/file2.txt", name="file2.txt",
             decoded_content=b"content2",
             encoding="utf-8", sha="sha2", size=8, type="file",
             url="url2", html_url="html2", git_url="git2", download_url="download2")
    ]
    mock_repository.get_contents.return_value = mock_content_files

    result = await file_manager.get_file_contents(config)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].path == "test/file1.txt"
    assert result[0].content == "content1"
    assert result[1].path == "test/file2.txt"
    assert result[1].content == "content2" 