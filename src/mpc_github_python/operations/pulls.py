"""Pulls module for GitHub pull request operations."""

from typing import Dict, List, Optional, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field
from github.Repository import Repository as GithubRepository
from github.PullRequest import PullRequest
from github.PullRequestReview import PullRequestReview
from github.GithubObject import NotSet

class PullRequestFile(BaseModel):
    """Represents a file in a pull request."""
    sha: str = Field(..., description="SHA of the file")
    filename: str = Field(..., description="Name of the file")
    status: Literal["added", "removed", "modified", "renamed", "copied", "changed", "unchanged"]
    additions: int = Field(..., description="Number of additions")
    deletions: int = Field(..., description="Number of deletions")
    changes: int = Field(..., description="Total number of changes")
    blob_url: str = Field(..., description="URL to the file's blob")
    raw_url: str = Field(..., description="URL to the raw file")
    contents_url: str = Field(..., description="URL to the file's contents")
    patch: Optional[str] = Field(None, description="The file's patch")

class StatusCheck(BaseModel):
    """Represents a status check."""
    url: str = Field(..., description="URL of the status check")
    state: Literal["error", "failure", "pending", "success"]
    description: Optional[str] = Field(None, description="Description of the status")
    target_url: Optional[str] = Field(None, description="URL to the status details")
    context: str = Field(..., description="Context of the status check")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class CombinedStatus(BaseModel):
    """Represents combined status checks."""
    state: Literal["error", "failure", "pending", "success"]
    statuses: List[StatusCheck] = Field(..., description="List of status checks")
    sha: str = Field(..., description="SHA of the commit")
    total_count: int = Field(..., description="Total number of status checks")

class PullRequestComment(BaseModel):
    """Represents a pull request comment."""
    id: int = Field(..., description="Comment ID")
    body: str = Field(..., description="Comment body")
    path: Optional[str] = Field(None, description="File path")
    position: Optional[int] = Field(None, description="Position in the diff")
    commit_id: str = Field(..., description="SHA of the commit")

class CreatePullRequestConfig(BaseModel):
    """Configuration for creating a pull request."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    title: str = Field(..., description="Pull request title")
    body: Optional[str] = Field(None, description="Pull request body")
    head: str = Field(..., description="Head branch")
    base: str = Field(..., description="Base branch")
    draft: Optional[bool] = Field(False, description="Whether to create as draft")
    maintainer_can_modify: Optional[bool] = Field(True, description="Allow maintainer modifications")

class GetPullRequestConfig(BaseModel):
    """Configuration for getting a pull request."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pull_number: int = Field(..., description="Pull request number")

class ListPullRequestsConfig(BaseModel):
    """Configuration for listing pull requests."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    state: Optional[Literal["open", "closed", "all"]] = Field(None, description="PR state")
    head: Optional[str] = Field(None, description="Head branch filter")
    base: Optional[str] = Field(None, description="Base branch filter")
    sort: Optional[Literal["created", "updated", "popularity", "long-running"]] = Field(None)
    direction: Optional[Literal["asc", "desc"]] = Field(None, description="Sort direction")
    per_page: Optional[int] = Field(None, description="Results per page")
    page: Optional[int] = Field(None, description="Page number")

class CreateReviewConfig(BaseModel):
    """Configuration for creating a review."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pull_number: int = Field(..., description="Pull request number")
    commit_id: Optional[str] = Field(None, description="Commit SHA to review")
    body: str = Field(..., description="Review body")
    event: Literal["APPROVE", "REQUEST_CHANGES", "COMMENT"] = Field(..., description="Review action")
    comments: Optional[List[Dict[str, Any]]] = Field(None, description="Review comments")

class MergePullRequestConfig(BaseModel):
    """Configuration for merging a pull request."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pull_number: int = Field(..., description="Pull request number")
    commit_title: Optional[str] = Field(None, description="Merge commit title")
    commit_message: Optional[str] = Field(None, description="Merge commit message")
    merge_method: Optional[Literal["merge", "squash", "rebase"]] = Field(None)

class UpdateBranchConfig(BaseModel):
    """Configuration for updating a pull request branch."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pull_number: int = Field(..., description="Pull request number")
    expected_head_sha: Optional[str] = Field(None, description="Expected head SHA")

class PullManager:
    """Manages GitHub pull request operations."""
    
    def __init__(self, repository: GithubRepository) -> None:
        """Initialize the pull request manager.
        
        Args:
            repository: GitHub repository to operate on
        """
        self.repository = repository
    
    async def get_pull_request(
        self,
        config: GetPullRequestConfig,
    ) -> PullRequest:
        """Get a pull request by number.
        
        Args:
            config: Pull request configuration
            
        Returns:
            The pull request
        """
        # Validate config
        config = GetPullRequestConfig.model_validate(config)
        return self.repository.get_pull(config.pull_number)
    
    async def create_pull_request(
        self,
        config: CreatePullRequestConfig,
    ) -> PullRequest:
        """Create a new pull request.
        
        Args:
            config: Pull request configuration
            
        Returns:
            The created pull request
        """
        # Validate config
        config = CreatePullRequestConfig.model_validate(config)
        
        return self.repository.create_pull(
            title=config.title,
            body=config.body if config.body else NotSet,
            head=config.head,
            base=config.base,
            draft=config.draft,
            maintainer_can_modify=config.maintainer_can_modify,
        )
    
    async def list_pull_requests(
        self,
        config: ListPullRequestsConfig,
    ) -> List[PullRequest]:
        """List pull requests in the repository.
        
        Args:
            config: List configuration
            
        Returns:
            List of pull requests
        """
        # Validate config
        config = ListPullRequestsConfig.model_validate(config)
        
        # Set up parameters
        state = config.state if config.state is not None else NotSet
        head = config.head if config.head is not None else NotSet
        base = config.base if config.base is not None else NotSet
        sort = config.sort if config.sort is not None else NotSet
        direction = config.direction if config.direction is not None else NotSet
        
        # Get pull requests with pagination
        pulls = self.repository.get_pulls(
            state=state,
            head=head,
            base=base,
            sort=sort,
            direction=direction,
        )
        
        # Apply pagination if specified
        if config.page is not None:
            pulls = pulls.get_page(config.page)
        elif config.per_page is not None:
            pulls = list(pulls)[:config.per_page]
        else:
            pulls = list(pulls)
        
        return pulls
    
    async def create_review(
        self,
        config: CreateReviewConfig,
    ) -> PullRequestReview:
        """Create a pull request review.
        
        Args:
            config: Review configuration
            
        Returns:
            The created review
        """
        # Validate config
        config = CreateReviewConfig.model_validate(config)
        
        pull = await self.get_pull_request(GetPullRequestConfig(
            owner=config.owner,
            repo=config.repo,
            pull_number=config.pull_number,
        ))
        
        commit_id = config.commit_id if config.commit_id else NotSet
        comments = config.comments or []
        
        return pull.create_review(
            commit_id=commit_id,
            body=config.body,
            event=config.event,
            comments=comments,
        )
    
    async def merge_pull_request(
        self,
        config: MergePullRequestConfig,
    ) -> Dict[str, Any]:
        """Merge a pull request.
        
        Args:
            config: Merge configuration
            
        Returns:
            Merge result information
        """
        # Validate config
        config = MergePullRequestConfig.model_validate(config)
        
        pull = await self.get_pull_request(GetPullRequestConfig(
            owner=config.owner,
            repo=config.repo,
            pull_number=config.pull_number,
        ))
        
        commit_title = config.commit_title if config.commit_title else NotSet
        commit_message = config.commit_message if config.commit_message else NotSet
        merge_method = config.merge_method if config.merge_method else NotSet
        
        result = pull.merge(
            commit_title=commit_title,
            commit_message=commit_message,
            merge_method=merge_method,
        )
        
        return {
            "sha": result.sha,
            "merged": result.merged,
            "message": result.message,
        }
    
    async def get_pull_request_files(
        self,
        config: GetPullRequestConfig,
    ) -> List[PullRequestFile]:
        """Get files in a pull request.
        
        Args:
            config: Pull request configuration
            
        Returns:
            List of files
        """
        # Validate config
        config = GetPullRequestConfig.model_validate(config)
        
        pull = await self.get_pull_request(config)
        files = pull.get_files()
        
        return [
            PullRequestFile(
                sha=f.sha,
                filename=f.filename,
                status=f.status,
                additions=f.additions,
                deletions=f.deletions,
                changes=f.changes,
                blob_url=f.blob_url,
                raw_url=f.raw_url,
                contents_url=f.contents_url,
                patch=f.patch if hasattr(f, "patch") else None,
            )
            for f in files
        ]
    
    async def get_pull_request_status(
        self,
        config: GetPullRequestConfig,
    ) -> CombinedStatus:
        """Get status checks for a pull request.
        
        Args:
            config: Pull request configuration
            
        Returns:
            Combined status information
        """
        # Validate config
        config = GetPullRequestConfig.model_validate(config)
        
        pull = await self.get_pull_request(config)
        status = pull.get_combined_status()
        
        return CombinedStatus(
            state=status.state,
            statuses=[
                StatusCheck(
                    url=s.url,
                    state=s.state,
                    description=s.description,
                    target_url=s.target_url,
                    context=s.context,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
                for s in status.statuses
            ],
            sha=status.sha,
            total_count=status.total_count,
        )
    
    async def update_branch(
        self,
        config: UpdateBranchConfig,
    ) -> None:
        """Update a pull request branch.
        
        Args:
            config: Update configuration
        """
        # Validate config
        config = UpdateBranchConfig.model_validate(config)
        
        pull = await self.get_pull_request(GetPullRequestConfig(
            owner=config.owner,
            repo=config.repo,
            pull_number=config.pull_number,
        ))
        
        pull.update_branch(expected_head_sha=config.expected_head_sha)
    
    async def get_pull_request_comments(
        self,
        config: GetPullRequestConfig,
    ) -> List[PullRequestComment]:
        """Get comments on a pull request.
        
        Args:
            config: Pull request configuration
            
        Returns:
            List of comments
        """
        # Validate config
        config = GetPullRequestConfig.model_validate(config)
        
        pull = await self.get_pull_request(config)
        comments = pull.get_comments()
        
        return [
            PullRequestComment(
                id=c.id,
                body=c.body,
                path=c.path,
                position=c.position,
                commit_id=c.commit_id,
            )
            for c in comments
        ]
    
    async def get_pull_request_reviews(
        self,
        config: GetPullRequestConfig,
    ) -> List[PullRequestReview]:
        """Get reviews on a pull request.
        
        Args:
            config: Pull request configuration
            
        Returns:
            List of reviews
        """
        # Validate config
        config = GetPullRequestConfig.model_validate(config)
        
        pull = await self.get_pull_request(config)
        return list(pull.get_reviews()) 