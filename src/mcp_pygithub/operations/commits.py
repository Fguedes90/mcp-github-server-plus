"""Commits module for GitHub commit operations."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from github.Repository import Repository as GithubRepository
from github.Commit import Commit
from github.GithubObject import NotSet

class CommitConfig(BaseModel):
    """Configuration for commit operations."""
    message: str = Field(..., description="Commit message")
    branch: Optional[str] = Field(None, description="Branch to commit to")
    committer: Optional[Dict[str, str]] = Field(None, description="Committer information")
    author: Optional[Dict[str, str]] = Field(None, description="Author information")

class ListCommitsConfig(BaseModel):
    """Configuration for listing commits."""
    branch: Optional[str] = Field(None, description="Branch to list commits from")
    path: Optional[str] = Field(None, description="Path to list commits for")
    page: Optional[int] = Field(None, description="Page number")
    per_page: Optional[int] = Field(None, description="Items per page")

class CommitManager:
    """Manages GitHub commit operations."""
    
    def __init__(self, repository: GithubRepository) -> None:
        """Initialize the commit manager.
        
        Args:
            repository: GitHub repository to operate on
        """
        self.repository = repository
    
    async def get_commit(self, sha: str) -> Commit:
        """Get a commit by SHA.
        
        Args:
            sha: Commit SHA
            
        Returns:
            The commit
        """
        return self.repository.get_commit(sha)
    
    async def list_commits(
        self,
        config: ListCommitsConfig,
    ) -> List[Commit]:
        """List commits in the repository.
        
        Args:
            config: List configuration
            
        Returns:
            List of commits
        """
        # Validate config
        config = ListCommitsConfig.model_validate(config)
        
        # Set up parameters
        branch = config.branch if config.branch is not None else NotSet
        path = config.path if config.path is not None else NotSet
        page = config.page if config.page is not None else NotSet
        per_page = config.per_page if config.per_page is not None else NotSet
        
        # Get commits with pagination
        commits = self.repository.get_commits(
            sha=branch,
            path=path,
        )
        
        # Apply pagination if specified
        if page is not NotSet:
            commits = commits.get_page(page)
        elif per_page is not NotSet:
            commits = list(commits)[:per_page]
        else:
            commits = list(commits)
        
        return commits
    
    async def compare_commits(
        self,
        base: str,
        head: str,
    ) -> Dict[str, List[Commit]]:
        """Compare two commits.
        
        Args:
            base: Base commit SHA or branch
            head: Head commit SHA or branch
            
        Returns:
            Dictionary with ahead_by, behind_by, and commits
        """
        comparison = self.repository.compare(base, head)
        return {
            "ahead_by": comparison.ahead_by,
            "behind_by": comparison.behind_by,
            "commits": list(comparison.commits),
        } 