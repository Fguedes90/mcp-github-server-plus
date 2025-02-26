"""Module for managing GitHub pull requests."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from github.PullRequest import PullRequest as GithubPullRequest
from github.Repository import Repository as GithubRepository
from github.PullRequestReview import PullRequestReview
from github.GithubObject import NotSet
from mcp_pygithub.common.auth import GitHubClientFactory, DefaultGitHubClientFactory

@dataclass
class PullRequestConfig:
    """Configuration for creating or updating a pull request."""
    title: str
    body: Optional[str] = None
    head: Optional[str] = None
    base: Optional[str] = None
    draft: bool = False
    maintainer_can_modify: bool = True

class PullRequestManager:
    """Manager for GitHub pull request operations."""

    def __init__(self, repository: GithubRepository, factory: Optional[GitHubClientFactory] = None) -> None:
        """Initialize the pull request manager.
        
        Args:
            repository: The GitHub repository to manage pull requests for.
            factory: Optional GitHub client factory for authentication.
        """
        self._repository = repository
        self._factory = factory or DefaultGitHubClientFactory()

    async def get_pull_request(self, number: int) -> GithubPullRequest:
        """Get a pull request by number.
        
        Args:
            number: The pull request number.
            
        Returns:
            The GitHub pull request.
            
        Raises:
            Exception: If the pull request is not found.
        """
        return self._repository.get_pull(number)

    async def create_pull_request(
        self,
        title: str,
        body: str,
        head: str,
        base: str,
        draft: bool = False,
        maintainer_can_modify: bool = True
    ) -> Dict[str, Any]:
        """Create a pull request.

        Args:
            title: Pull request title
            body: Pull request body
            head: Head branch
            base: Base branch
            draft: Whether this is a draft pull request
            maintainer_can_modify: Whether maintainers can modify the pull request

        Returns:
            Created pull request
        """
        pr = await self._repository.create_pull(
            title=title,
            body=body,
            head=head,
            base=base,
            draft=draft,
            maintainer_can_modify=maintainer_can_modify
        )
        
        return {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "head": {"ref": pr.head.ref},
            "base": {"ref": pr.base.ref},
            "draft": pr.draft,
            "maintainer_can_modify": pr.maintainer_can_modify
        }

    async def update_pull_request(self, number: int, config: PullRequestConfig) -> GithubPullRequest:
        """Update an existing pull request.
        
        Args:
            number: The pull request number.
            config: The pull request configuration.
            
        Returns:
            The updated GitHub pull request.
            
        Raises:
            Exception: If the pull request is not found.
        """
        pull_request = await self.get_pull_request(number)
        
        # Update fields that are set in config
        if config.title is not None:
            pull_request.edit(title=config.title)
        if config.body is not None:
            pull_request.edit(body=config.body)
        if config.base is not None:
            pull_request.edit(base=config.base)
        if config.maintainer_can_modify is not None:
            pull_request.edit(maintainer_can_modify=config.maintainer_can_modify)
            
        return pull_request

    async def list_pull_requests(
        self,
        state: str = "open",
        head: Optional[str] = None,
        base: Optional[str] = None,
        sort: str = "created",
        direction: str = "desc",
    ) -> List[GithubPullRequest]:
        """List pull requests in the repository.
        
        Args:
            state: Filter by pull request state ("open", "closed", "all").
            head: Filter by head branch.
            base: Filter by base branch.
            sort: Sort field ("created", "updated", "popularity", "long-running").
            direction: Sort direction ("asc", "desc").
            
        Returns:
            List of GitHub pull requests.
        """
        # Convert optional filters to NotSet if None
        head = head if head is not None else NotSet
        base = base if base is not None else NotSet
        
        return list(self._repository.get_pulls(
            state=state,
            head=head,
            base=base,
            sort=sort,
            direction=direction
        ))

    async def merge_pull_request(
        self,
        number: int,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
        merge_method: str = "merge",
    ) -> bool:
        """Merge a pull request.
        
        Args:
            number: The pull request number.
            commit_title: Optional title for the merge commit.
            commit_message: Optional message for the merge commit.
            merge_method: Merge method ("merge", "squash", "rebase").
            
        Returns:
            True if the pull request was merged successfully.
            
        Raises:
            Exception: If the pull request is not found or cannot be merged.
        """
        pull_request = await self.get_pull_request(number)
        
        # Convert optional parameters to NotSet if None
        commit_title = commit_title if commit_title is not None else NotSet
        commit_message = commit_message if commit_message is not None else NotSet
        
        return pull_request.merge(
            commit_title=commit_title,
            commit_message=commit_message,
            merge_method=merge_method
        )

    async def create_review(
        self,
        number: int,
        body: str,
        event: str = "COMMENT",
        comments: Optional[List[Dict[str, Any]]] = None,
    ) -> PullRequestReview:
        """Create a review on a pull request.
        
        Args:
            number: The pull request number.
            body: The review body text.
            event: Review event type ("APPROVE", "REQUEST_CHANGES", "COMMENT").
            comments: Optional list of review comments.
            
        Returns:
            The created pull request review.
            
        Raises:
            Exception: If the pull request is not found.
        """
        pull_request = await self.get_pull_request(number)
        
        # Convert optional parameters to NotSet if None
        comments = comments if comments is not None else NotSet
        
        return pull_request.create_review(
            body=body,
            event=event,
            comments=comments
        )

    async def request_review(self, number: int, reviewers: List[str]) -> None:
        """Request reviews for a pull request.
        
        Args:
            number: The pull request number.
            reviewers: List of usernames to request reviews from.
            
        Raises:
            Exception: If the pull request is not found.
        """
        pull_request = await self.get_pull_request(number)
        pull_request.create_review_request(reviewers=reviewers)

    async def remove_review_request(self, number: int, reviewers: List[str]) -> None:
        """Remove review requests from a pull request.
        
        Args:
            number: The pull request number.
            reviewers: List of usernames to remove review requests from.
            
        Raises:
            Exception: If the pull request is not found.
        """
        pull_request = await self.get_pull_request(number)
        pull_request.delete_review_request(reviewers=reviewers)

    async def update_branch(self, number: int) -> bool:
        """Update a pull request's branch with the latest changes from the base branch.
        
        Args:
            number: The pull request number.
            
        Returns:
            True if the branch was updated successfully.
            
        Raises:
            Exception: If the pull request is not found or cannot be updated.
        """
        pull_request = await self.get_pull_request(number)
        return pull_request.update_branch()

    async def close_pull_request(self, number: int) -> GithubPullRequest:
        """Close a pull request.
        
        Args:
            number: The pull request number.
            
        Returns:
            The closed GitHub pull request.
            
        Raises:
            Exception: If the pull request is not found.
        """
        pull_request = await self.get_pull_request(number)
        pull_request.edit(state="closed")
        return pull_request

    async def reopen_pull_request(self, number: int) -> GithubPullRequest:
        """Reopen a closed pull request.
        
        Args:
            number: The pull request number.
            
        Returns:
            The reopened GitHub pull request.
            
        Raises:
            Exception: If the pull request is not found.
        """
        pull_request = await self.get_pull_request(number)
        pull_request.edit(state="open")
        return pull_request 