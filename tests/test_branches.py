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
from mcp_github_server_plus.repository.repository import RepositoryConfig, RepositoryManager
from mcp_github_server_plus.branches.branches import BranchManager, BranchProtectionConfig
from mcp_github_server_plus.files.files import FileManager

# Check if we have a GitHub token for live testing
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
TEST_WITH_LIVE_API = GITHUB_TOKEN is not None

@pytest.fixture
def config() -> RepositoryConfig:
    """Create a test repository configuration."""
    if not TEST_WITH_LIVE_API:
        pytest.skip("No GitHub token available")
    return RepositoryConfig(
        token=GITHUB_TOKEN,
        owner=None,  # Will be set from authenticated user
        name=None,  # Will be set per test
    )

@pytest.fixture
def github_client() -> Github:
    """Create a GitHub client."""
    if not TEST_WITH_LIVE_API:
        pytest.skip("No GitHub token available")
    return Github(GITHUB_TOKEN)

@pytest.fixture
async def test_repo(config: RepositoryConfig, github_client: Github) -> GithubRepository:
    """Create a test repository for branch operations."""
    # Create unique repository name
    unique_id = str(uuid.uuid4())[:8]
    repo_name = f"test-branches-repo-{unique_id}"
    repo_manager = RepositoryManager(config)
    
    try:
        # Create test repository
        repo = await repo_manager.create_repository(repo_name)
        
        # Create initial commit
        file_manager = FileManager(repo)
        await file_manager.create_file(
            path="README.md",
            content="# Test Repository\nCreated for branch testing.",
            message="Initial commit"
        )
        
        yield repo
    finally:
        # Clean up
        try:
            repo = github_client.get_repo(f"{github_client.get_user().login}/{repo_name}")
            repo.delete()
        except:
            pass

@pytest.mark.asyncio
async def test_get_branch(test_repo: GithubRepository) -> None:
    """Test getting a branch."""
    manager = BranchManager(test_repo)
    
    # Get default branch
    branch = await manager.get_branch(test_repo.default_branch)
    assert branch.name == test_repo.default_branch

@pytest.mark.asyncio
async def test_create_branch(test_repo: GithubRepository) -> None:
    """Test branch creation."""
    manager = BranchManager(test_repo)
    branch_name = "test-branch"
    
    try:
        # Create new branch
        branch = await manager.create_branch(branch_name)
        assert branch.name == branch_name
        
        # Verify it exists
        found_branch = await manager.get_branch(branch_name)
        assert found_branch.name == branch_name
    finally:
        # Clean up
        try:
            await manager.delete_branch(branch_name)
        except:
            pass

@pytest.mark.asyncio
async def test_delete_branch(test_repo: GithubRepository) -> None:
    """Test branch deletion."""
    manager = BranchManager(test_repo)
    branch_name = "branch-to-delete"
    
    # Create branch to delete
    await manager.create_branch(branch_name)
    
    # Delete it
    await manager.delete_branch(branch_name)
    
    # Verify it's gone
    with pytest.raises(Exception):
        await manager.get_branch(branch_name)

@pytest.mark.asyncio
async def test_protect_branch(test_repo: GithubRepository) -> None:
    """Test branch protection."""
    manager = BranchManager(test_repo)
    
    # Configure protection rules
    config = BranchProtectionConfig(
        required_status_checks=["test-status"],
        enforce_admins=True,
        required_pull_request_reviews=True,
        required_approving_review_count=1,
    )
    
    # Apply protection to default branch
    protection = await manager.protect_branch(test_repo.default_branch, config)
    assert isinstance(protection, BranchProtection)
    
    # Clean up
    await manager.remove_protection(test_repo.default_branch)

@pytest.mark.asyncio
async def test_list_branches(test_repo: GithubRepository) -> None:
    """Test listing branches."""
    manager = BranchManager(test_repo)
    branch_names = ["test-branch-1", "test-branch-2"]
    
    try:
        # Create test branches
        for name in branch_names:
            await manager.create_branch(name)
        
        # List all branches
        branches = await manager.list_branches()
        assert len(branches) >= len(branch_names) + 1  # +1 for default branch
        assert all(isinstance(branch, GithubBranch) for branch in branches)
        assert all(branch.name in [*branch_names, test_repo.default_branch] for branch in branches)
    finally:
        # Clean up
        for name in branch_names:
            try:
                await manager.delete_branch(name)
            except:
                pass

@pytest.mark.asyncio
async def test_get_branch_empty_repo() -> None:
    """Test getting a branch in an empty repository."""
    # Create mock repository
    mock_repo = Mock(spec=GithubRepository)
    mock_repo.default_branch = "main"
    
    # Mock get_commits to return empty list first time
    mock_repo.get_commits.return_value = []
    
    # Mock create_file
    mock_content = Mock()
    mock_content.sha = "test-sha"
    mock_repo.create_file.return_value = (mock_content, None)
    
    # Mock get_branch to fail first time, then succeed
    mock_branch = Mock(spec=GithubBranch)
    mock_branch.name = "main"
    mock_repo.get_branch.side_effect = [
        Exception("Branch not found"),  # First call fails
        mock_branch  # Second call succeeds
    ]
    
    manager = BranchManager(mock_repo)
    
    # This should create an initial commit and return the branch
    branch = await manager.get_branch("main")
    assert branch.name == "main"
    
    # Verify create_file was called
    mock_repo.create_file.assert_called_once_with(
        path="README.md",
        message="Initial commit",
        content="# Repository\nInitialized by BranchManager",
        branch="main",
    )

@pytest.mark.asyncio
async def test_get_branch_not_found(test_repo: GithubRepository) -> None:
    """Test getting a non-existent branch."""
    manager = BranchManager(test_repo)
    
    with pytest.raises(Exception):
        await manager.get_branch("non-existent-branch") 