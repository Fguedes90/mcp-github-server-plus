"""Module for managing GitHub issues."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from github.Issue import Issue as GithubIssue
from github.Repository import Repository as GithubRepository
from github.Label import Label as GithubLabel
from github.Milestone import Milestone as GithubMilestone
from github.GithubObject import NotSet
from mcp_pygithub.common.auth import GitHubClientFactory, DefaultGitHubClientFactory

@dataclass
class IssueConfig:
    """Configuration for creating or updating an issue."""
    title: str
    body: Optional[str] = None
    assignees: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    milestone: Optional[int] = None
    state: Optional[str] = None

class IssueManager:
    """Manager for GitHub issue operations."""

    def __init__(self, repository: GithubRepository, factory: Optional[GitHubClientFactory] = None) -> None:
        """Initialize the issue manager.
        
        Args:
            repository: The GitHub repository to manage issues for.
            factory: Optional GitHub client factory for authentication.
        """
        self._repository = repository
        self._factory = factory or DefaultGitHubClientFactory()

    async def get_issue(self, number: int) -> GithubIssue:
        """Get an issue by number.
        
        Args:
            number: The issue number.
            
        Returns:
            The GitHub issue.
            
        Raises:
            Exception: If the issue is not found.
        """
        return self._repository.get_issue(number)

    async def create_issue(
        self,
        config: IssueConfig
    ) -> GithubIssue:
        """Create a new issue.
        
        Args:
            config: The issue configuration.
            
        Returns:
            Created GitHub issue.
        """
        issue = self._repository.create_issue(
            title=config.title,
            body=config.body if config.body else "",
            labels=config.labels if config.labels else [],
            assignees=config.assignees if config.assignees else [],
            milestone=config.milestone if config.milestone else NotSet
        )
        return issue

    async def update_issue(self, number: int, config: IssueConfig) -> GithubIssue:
        """Update an existing issue.
        
        Args:
            number: The issue number.
            config: The issue configuration.
            
        Returns:
            The updated GitHub issue.
            
        Raises:
            Exception: If the issue is not found.
        """
        issue = await self.get_issue(number)
        
        # Update fields that are set in config
        if config.title is not None:
            issue.edit(title=config.title)
        if config.body is not None:
            issue.edit(body=config.body)
        if config.assignees is not None:
            issue.edit(assignees=config.assignees)
        if config.labels is not None:
            issue.edit(labels=config.labels)
        if config.milestone is not None:
            issue.edit(milestone=config.milestone)
        if config.state is not None:
            issue.edit(state=config.state)
            
        return issue

    async def close_issue(self, number: int) -> GithubIssue:
        """Close an issue.
        
        Args:
            number: The issue number.
            
        Returns:
            The closed GitHub issue.
            
        Raises:
            Exception: If the issue is not found.
        """
        issue = await self.get_issue(number)
        issue.edit(state="closed")
        return issue

    async def reopen_issue(self, number: int) -> GithubIssue:
        """Reopen a closed issue.
        
        Args:
            number: The issue number.
            
        Returns:
            The reopened GitHub issue.
            
        Raises:
            Exception: If the issue is not found.
        """
        issue = await self.get_issue(number)
        issue.edit(state="open")
        return issue

    async def list_issues(
        self,
        state: str = "open",
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        milestone: Optional[int] = None,
    ) -> List[GithubIssue]:
        """List issues in the repository.
        
        Args:
            state: Filter by issue state ("open", "closed", "all").
            labels: Filter by label names.
            assignee: Filter by assignee username.
            milestone: Filter by milestone number.
            
        Returns:
            List of GitHub issues.
        """
        # Convert optional filters to NotSet if None
        labels = labels if labels is not None else NotSet
        assignee = assignee if assignee is not None else NotSet
        milestone = milestone if milestone is not None else NotSet
        
        return list(self._repository.get_issues(
            state=state,
            labels=labels,
            assignee=assignee,
            milestone=milestone
        ))

    async def add_labels(self, number: int, labels: List[str]) -> List[GithubLabel]:
        """Add labels to an issue.
        
        Args:
            number: The issue number.
            labels: List of label names to add.
            
        Returns:
            List of added GitHub labels.
            
        Raises:
            Exception: If the issue is not found.
        """
        issue = await self.get_issue(number)
        return list(issue.add_to_labels(*labels))

    async def remove_labels(self, number: int, labels: List[str]) -> None:
        """Remove labels from an issue.
        
        Args:
            number: The issue number.
            labels: List of label names to remove.
            
        Raises:
            Exception: If the issue is not found.
        """
        issue = await self.get_issue(number)
        for label in labels:
            issue.remove_from_labels(label)

    async def set_milestone(self, number: int, milestone: Optional[GithubMilestone]) -> GithubIssue:
        """Set the milestone for an issue.
        
        Args:
            number: The issue number.
            milestone: The milestone to set, or None to clear.
            
        Returns:
            The updated GitHub issue.
            
        Raises:
            Exception: If the issue is not found.
        """
        issue = await self.get_issue(number)
        issue.edit(milestone=milestone or NotSet)
        return issue

    async def add_assignees(self, number: int, assignees: List[str]) -> GithubIssue:
        """Add assignees to an issue.
        
        Args:
            number: The issue number.
            assignees: List of usernames to assign.
            
        Returns:
            The updated GitHub issue.
            
        Raises:
            Exception: If the issue is not found.
        """
        issue = await self.get_issue(number)
        issue.add_to_assignees(*assignees)
        return issue

    async def remove_assignees(self, number: int, assignees: List[str]) -> GithubIssue:
        """Remove assignees from an issue.
        
        Args:
            number: The issue number.
            assignees: List of usernames to remove.
            
        Returns:
            The updated GitHub issue.
            
        Raises:
            Exception: If the issue is not found.
        """
        issue = await self.get_issue(number)
        issue.remove_from_assignees(*assignees)
        return issue 