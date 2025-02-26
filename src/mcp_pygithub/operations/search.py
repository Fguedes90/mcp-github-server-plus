"""Module for searching GitHub repositories."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from github import Github, Repository
from github.Repository import Repository as GithubRepository
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.ContentFile import ContentFile
from github.GithubObject import NotSet
from mcp_pygithub.common.auth import GitHubClientFactory, DefaultGitHubClientFactory
from mcp_pygithub.common.errors import SearchError
import logging

logger = logging.getLogger(__name__)

@dataclass
class SearchConfig:
    """Configuration for search operations."""
    query: str
    path: Optional[str] = None
    extension: Optional[str] = None
    sort: Optional[str] = None
    order: Optional[str] = "desc"
    per_page: Optional[int] = 30
    page: Optional[int] = 1

class SearchManager:
    """Manager for GitHub search operations."""

    def __init__(self, repository: GithubRepository, factory: Optional[GitHubClientFactory] = None) -> None:
        """Initialize the search manager.
        
        Args:
            repository: The GitHub repository to search in.
            factory: Optional GitHub client factory for authentication.
        """
        self._repository = repository
        self._factory = factory or DefaultGitHubClientFactory()

    async def search_issues(self, config: SearchConfig) -> List[Issue]:
        """Search for issues in the repository.
        
        Args:
            config: Search configuration.
            
        Returns:
            List of matching issues.
        """
        # Validate config
        config = SearchConfig(**config.__dict__)
        
        # Build query
        query = f"repo:{self._repository.full_name} {config.query}"
        
        # Search issues
        issues = self._repository.get_issues(
            sort=config.sort,
            direction=config.order,
            per_page=config.per_page,
            page=config.page,
        )
        
        return list(issues)

    async def search_pulls(self, config: SearchConfig) -> List[PullRequest]:
        """Search for pull requests in the repository.
        
        Args:
            config: Search configuration.
            
        Returns:
            List of matching pull requests.
        """
        # Validate config
        config = SearchConfig(**config.__dict__)
        
        # Build query
        query = f"repo:{self._repository.full_name} {config.query}"
        
        # Search pull requests
        pulls = self._repository.get_pulls(
            sort=config.sort,
            direction=config.order,
            per_page=config.per_page,
            page=config.page,
        )
        
        return list(pulls)

    async def search_code(self, config: SearchConfig) -> List[Dict[str, str]]:
        """Search for code in the repository.

        Args:
            config: Search configuration.

        Returns:
            List of matching code files.
        """
        config = SearchConfig(**config.__dict__)
        results = []

        try:
            path = config.path if config.path else ""
            contents = self._repository.get_contents(path)
            
            if not isinstance(contents, list):
                contents = [contents]

            for content in contents:
                if content.type == "file":
                    if (not config.path or config.path in content.path) and \
                       (not config.extension or content.path.endswith(config.extension)):
                        results.append({
                            "path": content.path,
                            "content": content.decoded_content.decode('utf-8'),
                            "sha": content.sha,
                            "encoding": content.encoding,
                            "size": content.size,
                            "type": content.type,
                            "url": content.url,
                            "html_url": content.html_url,
                            "git_url": content.git_url,
                            "download_url": content.download_url
                        })
        except Exception as e:
            logger.error(f"Error searching code: {e}")
            raise SearchError(f"Failed to search code: {e}")

        return results

    async def search_commits(self, config: SearchConfig) -> List[str]:
        """Search for commits in the repository.
        
        Args:
            config: Search configuration.
            
        Returns:
            List of matching commit SHAs.
        """
        # Validate config
        config = SearchConfig(**config.__dict__)
        
        # Build query
        query = f"repo:{self._repository.full_name} {config.query}"
        
        # Search commits
        commits = self._repository.get_commits(
            sha=None,
            path=None,
            since=None,
            until=None,
            author=None,
            per_page=config.per_page,
            page=config.page,
        )
        
        return [commit.sha for commit in commits] 