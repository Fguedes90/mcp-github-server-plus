"""Search module for GitHub search operations."""

from typing import Dict, List, Optional, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field
from github import Github
from github.PaginatedList import PaginatedList
from github.Repository import Repository
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.GithubObject import NotSet

class BaseSearchConfig(BaseModel):
    """Base configuration for search operations."""
    query: str = Field(..., description="Search query")
    order: Optional[Literal["asc", "desc"]] = Field(None, description="Sort order")
    page: Optional[int] = Field(None, description="Page number", ge=1)
    per_page: Optional[int] = Field(None, description="Results per page", ge=1, le=100)

class SearchUsersConfig(BaseSearchConfig):
    """Configuration for user search operations."""
    sort: Optional[Literal["followers", "repositories", "joined"]] = Field(None, description="Sort field")

class SearchIssuesConfig(BaseSearchConfig):
    """Configuration for issue search operations."""
    sort: Optional[Literal[
        "comments",
        "reactions",
        "reactions-+1",
        "reactions--1",
        "reactions-smile",
        "reactions-thinking_face",
        "reactions-heart",
        "reactions-tada",
        "interactions",
        "created",
        "updated"
    ]] = Field(None, description="Sort field")

class SearchCodeConfig(BaseSearchConfig):
    """Configuration for code search operations."""
    pass

class SearchManager:
    """Manages GitHub search operations."""
    
    def __init__(self, github: Github) -> None:
        """Initialize the search manager.
        
        Args:
            github: GitHub client instance
        """
        self.github = github
    
    async def search_repositories(
        self,
        config: BaseSearchConfig,
    ) -> PaginatedList:
        """Search for repositories.
        
        Args:
            config: Search configuration
            
        Returns:
            List of matching repositories
        """
        # Validate config
        config = BaseSearchConfig.model_validate(config)
        
        # Set up parameters
        order = config.order if config.order is not None else NotSet
        page = config.page if config.page is not None else NotSet
        per_page = config.per_page if config.per_page is not None else NotSet
        
        # Get repositories with pagination
        repos = self.github.search_repositories(
            query=config.query,
            order=order,
        )
        
        # Apply pagination if specified
        if page is not NotSet:
            repos = repos.get_page(page)
        elif per_page is not NotSet:
            repos = list(repos)[:per_page]
        else:
            repos = list(repos)
        
        return repos
    
    async def search_issues(
        self,
        config: SearchIssuesConfig,
    ) -> PaginatedList:
        """Search for issues and pull requests.
        
        Args:
            config: Search configuration
            
        Returns:
            List of matching issues and pull requests
        """
        # Validate config
        config = SearchIssuesConfig.model_validate(config)
        
        # Set up parameters
        sort = config.sort if config.sort is not None else NotSet
        order = config.order if config.order is not None else NotSet
        page = config.page if config.page is not None else NotSet
        per_page = config.per_page if config.per_page is not None else NotSet
        
        # Get issues with pagination
        issues = self.github.search_issues(
            query=config.query,
            sort=sort,
            order=order,
        )
        
        # Apply pagination if specified
        if page is not NotSet:
            issues = issues.get_page(page)
        elif per_page is not NotSet:
            issues = list(issues)[:per_page]
        else:
            issues = list(issues)
        
        return issues
    
    async def search_code(
        self,
        config: SearchCodeConfig,
    ) -> PaginatedList:
        """Search for code.
        
        Args:
            config: Search configuration
            
        Returns:
            List of matching code files
        """
        # Validate config
        config = SearchCodeConfig.model_validate(config)
        
        # Set up parameters
        order = config.order if config.order is not None else NotSet
        page = config.page if config.page is not None else NotSet
        per_page = config.per_page if config.per_page is not None else NotSet
        
        # Get code with pagination
        code = self.github.search_code(
            query=config.query,
            order=order,
        )
        
        # Apply pagination if specified
        if page is not NotSet:
            code = code.get_page(page)
        elif per_page is not NotSet:
            code = list(code)[:per_page]
        else:
            code = list(code)
        
        return code
    
    async def search_users(
        self,
        config: SearchUsersConfig,
    ) -> PaginatedList:
        """Search for users.
        
        Args:
            config: Search configuration
            
        Returns:
            List of matching users
        """
        # Validate config
        config = SearchUsersConfig.model_validate(config)
        
        # Set up parameters
        sort = config.sort if config.sort is not None else NotSet
        order = config.order if config.order is not None else NotSet
        page = config.page if config.page is not None else NotSet
        per_page = config.per_page if config.per_page is not None else NotSet
        
        # Get users with pagination
        users = self.github.search_users(
            query=config.query,
            sort=sort,
            order=order,
        )
        
        # Apply pagination if specified
        if page is not NotSet:
            users = users.get_page(page)
        elif per_page is not NotSet:
            users = list(users)[:per_page]
        else:
            users = list(users)
        
        return users 