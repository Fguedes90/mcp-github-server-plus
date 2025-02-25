"""Issues module for GitHub issue operations."""

from typing import Dict, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from github.Repository import Repository as GithubRepository
from github.Issue import Issue
from github.Label import Label
from github.GithubObject import NotSet

class GetIssueConfig(BaseModel):
    """Configuration for getting an issue."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    issue_number: int = Field(..., description="Issue number")

class IssueCommentConfig(BaseModel):
    """Configuration for issue comments."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    issue_number: int = Field(..., description="Issue number")
    body: str = Field(..., description="Comment body")

class CreateIssueConfig(BaseModel):
    """Configuration for creating an issue."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    title: str = Field(..., description="Issue title")
    body: Optional[str] = Field(None, description="Issue body")
    assignees: Optional[List[str]] = Field(None, description="List of assignees")
    milestone: Optional[int] = Field(None, description="Milestone number")
    labels: Optional[List[str]] = Field(None, description="List of labels")

class ListIssuesConfig(BaseModel):
    """Configuration for listing issues."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    direction: Optional[Literal["asc", "desc"]] = Field(None, description="Sort direction")
    labels: Optional[List[str]] = Field(None, description="Filter by labels")
    page: Optional[int] = Field(None, description="Page number")
    per_page: Optional[int] = Field(None, description="Items per page")
    since: Optional[datetime] = Field(None, description="Filter by date")
    sort: Optional[Literal["created", "updated", "comments"]] = Field(None, description="Sort field")
    state: Optional[Literal["open", "closed", "all"]] = Field(None, description="Issue state")

class UpdateIssueConfig(BaseModel):
    """Configuration for updating an issue."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    issue_number: int = Field(..., description="Issue number")
    title: Optional[str] = Field(None, description="New title")
    body: Optional[str] = Field(None, description="New body")
    assignees: Optional[List[str]] = Field(None, description="New assignees")
    milestone: Optional[int] = Field(None, description="New milestone")
    labels: Optional[List[str]] = Field(None, description="New labels")
    state: Optional[Literal["open", "closed"]] = Field(None, description="New state")

class IssueManager:
    """Manages GitHub issue operations."""
    
    def __init__(self, repository: GithubRepository) -> None:
        """Initialize the issue manager.
        
        Args:
            repository: GitHub repository to operate on
        """
        self.repository = repository
    
    async def get_issue(
        self,
        config: GetIssueConfig,
    ) -> Issue:
        """Get an issue by number.
        
        Args:
            config: Issue configuration
            
        Returns:
            The issue
        """
        # Validate config
        config = GetIssueConfig.model_validate(config)
        return self.repository.get_issue(config.issue_number)
    
    async def add_issue_comment(
        self,
        config: IssueCommentConfig,
    ) -> Dict[str, str]:
        """Add a comment to an issue.
        
        Args:
            config: Comment configuration
            
        Returns:
            Comment information
        """
        # Validate config
        config = IssueCommentConfig.model_validate(config)
        
        issue = await self.get_issue(GetIssueConfig(
            owner=config.owner,
            repo=config.repo,
            issue_number=config.issue_number,
        ))
        
        comment = issue.create_comment(config.body)
        return {
            "id": str(comment.id),
            "body": comment.body,
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
            "user": comment.user.login,
        }
    
    async def create_issue(
        self,
        config: CreateIssueConfig,
    ) -> Issue:
        """Create a new issue.
        
        Args:
            config: Issue configuration
            
        Returns:
            The created issue
        """
        # Validate config
        config = CreateIssueConfig.model_validate(config)
        
        labels = config.labels or []
        assignees = config.assignees or []
        milestone = config.milestone if config.milestone is not None else NotSet
        
        return self.repository.create_issue(
            title=config.title,
            body=config.body if config.body else NotSet,
            labels=labels,
            assignees=assignees,
            milestone=milestone,
        )
    
    async def list_issues(
        self,
        config: ListIssuesConfig,
    ) -> List[Issue]:
        """List issues in the repository.
        
        Args:
            config: List configuration
            
        Returns:
            List of issues
        """
        # Validate config
        config = ListIssuesConfig.model_validate(config)
        
        # Set up parameters
        state = config.state if config.state is not None else NotSet
        labels = config.labels if config.labels is not None else NotSet
        sort = config.sort if config.sort is not None else NotSet
        direction = config.direction if config.direction is not None else NotSet
        since = config.since if config.since is not None else NotSet
        
        # Get issues with pagination
        issues = self.repository.get_issues(
            state=state,
            labels=labels,
            sort=sort,
            direction=direction,
            since=since,
        )
        
        # Apply pagination if specified
        if config.page is not None:
            issues = issues.get_page(config.page)
        elif config.per_page is not None:
            issues = list(issues)[:config.per_page]
        else:
            issues = list(issues)
        
        return issues
    
    async def update_issue(
        self,
        config: UpdateIssueConfig,
    ) -> Issue:
        """Update an issue.
        
        Args:
            config: Update configuration
            
        Returns:
            The updated issue
        """
        # Validate config
        config = UpdateIssueConfig.model_validate(config)
        
        issue = await self.get_issue(GetIssueConfig(
            owner=config.owner,
            repo=config.repo,
            issue_number=config.issue_number,
        ))
        
        # Prepare update parameters
        title = config.title if config.title is not None else NotSet
        body = config.body if config.body is not None else NotSet
        labels = config.labels if config.labels is not None else NotSet
        assignees = config.assignees if config.assignees is not None else NotSet
        milestone = config.milestone if config.milestone is not None else NotSet
        state = config.state if config.state is not None else NotSet
        
        issue.edit(
            title=title,
            body=body,
            labels=labels,
            assignees=assignees,
            milestone=milestone,
            state=state,
        )
        return issue
    
    async def close_issue(self, issue: Issue) -> None:
        """Close an issue.
        
        Args:
            issue: Issue to close
        """
        issue.edit(state="closed")
    
    async def reopen_issue(self, issue: Issue) -> None:
        """Reopen an issue.
        
        Args:
            issue: Issue to reopen
        """
        issue.edit(state="open")
    
    async def list_issues(
        self,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None,
    ) -> List[Issue]:
        """List issues in the repository.
        
        Args:
            state: Issue state (open, closed, all)
            labels: Filter by labels
            assignee: Filter by assignee
            
        Returns:
            List of issues
        """
        state = state if state is not None else NotSet
        labels = labels if labels is not None else NotSet
        assignee = assignee if assignee is not None else NotSet
        
        return list(self.repository.get_issues(
            state=state,
            labels=labels,
            assignee=assignee,
        )) 