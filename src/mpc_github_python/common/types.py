"""Type definitions for GitHub operations."""

from typing import Dict, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

class GitHubUser(BaseModel):
    """GitHub user information."""
    login: str = Field(..., description="Username")
    name: Optional[str] = Field(None, description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    avatar_url: Optional[HttpUrl] = Field(None, description="Avatar URL")
    type: Literal["User", "Organization", "Bot"] = Field(..., description="Account type")
    site_admin: bool = Field(False, description="Whether the user is a site admin")
    html_url: HttpUrl = Field(..., description="GitHub profile URL")

class GitHubLabel(BaseModel):
    """GitHub label information."""
    name: str = Field(..., description="Label name")
    color: str = Field(..., description="Label color (hex)")
    description: Optional[str] = Field(None, description="Label description")
    default: bool = Field(False, description="Whether this is a default label")

class GitHubMilestone(BaseModel):
    """GitHub milestone information."""
    number: int = Field(..., description="Milestone number")
    title: str = Field(..., description="Milestone title")
    description: Optional[str] = Field(None, description="Milestone description")
    state: Literal["open", "closed"] = Field(..., description="Milestone state")
    due_on: Optional[datetime] = Field(None, description="Due date")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    closed_at: Optional[datetime] = Field(None, description="Closure timestamp")

class GitHubTeam(BaseModel):
    """GitHub team information."""
    id: int = Field(..., description="Team ID")
    name: str = Field(..., description="Team name")
    slug: str = Field(..., description="Team slug")
    description: Optional[str] = Field(None, description="Team description")
    privacy: Literal["secret", "closed"] = Field(..., description="Team privacy level")
    html_url: HttpUrl = Field(..., description="Team URL")

class GitHubOrganization(BaseModel):
    """GitHub organization information."""
    login: str = Field(..., description="Organization name")
    name: Optional[str] = Field(None, description="Organization display name")
    description: Optional[str] = Field(None, description="Organization description")
    email: Optional[str] = Field(None, description="Organization email")
    avatar_url: Optional[HttpUrl] = Field(None, description="Organization avatar URL")
    html_url: HttpUrl = Field(..., description="Organization URL")

class GitHubComment(BaseModel):
    """GitHub comment information."""
    id: int = Field(..., description="Comment ID")
    body: str = Field(..., description="Comment body")
    user: GitHubUser = Field(..., description="Comment author")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    html_url: HttpUrl = Field(..., description="Comment URL")

class GitHubCommit(BaseModel):
    """GitHub commit information."""
    sha: str = Field(..., description="Commit SHA")
    message: str = Field(..., description="Commit message")
    author: GitHubUser = Field(..., description="Commit author")
    committer: GitHubUser = Field(..., description="Commit committer")
    url: HttpUrl = Field(..., description="API URL")
    html_url: HttpUrl = Field(..., description="Web URL")
    parents: List[str] = Field(default_factory=list, description="Parent commit SHAs")
    created_at: datetime = Field(..., description="Creation timestamp")

class GitHubBranch(BaseModel):
    """GitHub branch information."""
    name: str = Field(..., description="Branch name")
    commit: GitHubCommit = Field(..., description="Latest commit")
    protected: bool = Field(False, description="Whether the branch is protected")
    protection_url: Optional[HttpUrl] = Field(None, description="Branch protection API URL")

class GitHubFile(BaseModel):
    """GitHub file information."""
    path: str = Field(..., description="File path")
    sha: str = Field(..., description="File SHA")
    size: int = Field(..., description="File size in bytes")
    content: Optional[str] = Field(None, description="File content")
    encoding: Optional[str] = Field(None, description="Content encoding")
    url: HttpUrl = Field(..., description="API URL")
    html_url: HttpUrl = Field(..., description="Web URL")
    git_url: HttpUrl = Field(..., description="Git URL")
    download_url: Optional[HttpUrl] = Field(None, description="Raw content URL")
    type: Literal["file", "dir", "symlink", "submodule"] = Field(..., description="File type")

class GitHubTree(BaseModel):
    """GitHub tree information."""
    sha: str = Field(..., description="Tree SHA")
    url: HttpUrl = Field(..., description="API URL")
    tree: List[GitHubFile] = Field(..., description="Tree entries")
    truncated: bool = Field(False, description="Whether the response was truncated")

class GitHubPullRequest(BaseModel):
    """GitHub pull request information."""
    number: int = Field(..., description="Pull request number")
    title: str = Field(..., description="Pull request title")
    body: Optional[str] = Field(None, description="Pull request body")
    state: Literal["open", "closed"] = Field(..., description="Pull request state")
    head: GitHubBranch = Field(..., description="Head branch")
    base: GitHubBranch = Field(..., description="Base branch")
    user: GitHubUser = Field(..., description="Pull request author")
    merged: bool = Field(False, description="Whether the PR is merged")
    mergeable: Optional[bool] = Field(None, description="Whether the PR can be merged")
    rebaseable: Optional[bool] = Field(None, description="Whether the PR can be rebased")
    merged_by: Optional[GitHubUser] = Field(None, description="User who merged the PR")
    comments: int = Field(0, description="Number of comments")
    commits: int = Field(0, description="Number of commits")
    additions: int = Field(0, description="Number of additions")
    deletions: int = Field(0, description="Number of deletions")
    changed_files: int = Field(0, description="Number of changed files")
    html_url: HttpUrl = Field(..., description="Web URL")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    closed_at: Optional[datetime] = Field(None, description="Closure timestamp")
    merged_at: Optional[datetime] = Field(None, description="Merge timestamp")

class GitHubIssue(BaseModel):
    """GitHub issue information."""
    number: int = Field(..., description="Issue number")
    title: str = Field(..., description="Issue title")
    body: Optional[str] = Field(None, description="Issue body")
    state: Literal["open", "closed"] = Field(..., description="Issue state")
    user: GitHubUser = Field(..., description="Issue author")
    labels: List[GitHubLabel] = Field(default_factory=list, description="Issue labels")
    assignees: List[GitHubUser] = Field(default_factory=list, description="Issue assignees")
    milestone: Optional[GitHubMilestone] = Field(None, description="Issue milestone")
    locked: bool = Field(False, description="Whether the issue is locked")
    comments: int = Field(0, description="Number of comments")
    html_url: HttpUrl = Field(..., description="Web URL")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    closed_at: Optional[datetime] = Field(None, description="Closure timestamp")
    closed_by: Optional[GitHubUser] = Field(None, description="User who closed the issue")

class GitHubWorkflow(BaseModel):
    """GitHub workflow information."""
    id: int = Field(..., description="Workflow ID")
    name: str = Field(..., description="Workflow name")
    state: Literal["active", "deleted", "disabled_fork", "disabled_inactivity", "disabled_manually"] = Field(..., description="Workflow state")
    path: str = Field(..., description="Workflow file path")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    url: HttpUrl = Field(..., description="API URL")
    html_url: HttpUrl = Field(..., description="Web URL")
    badge_url: HttpUrl = Field(..., description="Status badge URL")

class GitHubWorkflowRun(BaseModel):
    """GitHub workflow run information."""
    id: int = Field(..., description="Run ID")
    workflow_id: int = Field(..., description="Workflow ID")
    status: Literal["queued", "in_progress", "completed"] = Field(..., description="Run status")
    conclusion: Optional[Literal["success", "failure", "cancelled", "skipped", "timed_out", "action_required"]] = Field(None, description="Run conclusion")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    url: HttpUrl = Field(..., description="API URL")
    html_url: HttpUrl = Field(..., description="Web URL")
    logs_url: HttpUrl = Field(..., description="Logs URL") 