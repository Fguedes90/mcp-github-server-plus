"""Repository module for GitHub operations.

This module provides the core functionality for repository operations including:
- Repository creation
- Repository search
- Repository forking
- Repository management
"""

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from github import Github
from github.Repository import Repository as GithubRepository
from github.PaginatedList import PaginatedList
from github.GithubObject import NotSet

class RepositoryConfig(BaseModel):
    """Configuration for repository operations."""
    token: str = Field(..., description="GitHub personal access token")
    owner: Optional[str] = Field(None, description="Repository owner (username or organization)")
    name: Optional[str] = Field(None, description="Repository name")
    private: bool = Field(False, description="Whether the repository should be private")
    description: Optional[str] = Field(None, description="Repository description")

class CreateRepositoryConfig(BaseModel):
    """Configuration for creating a repository."""
    name: str = Field(..., description="Repository name")
    private: Optional[bool] = Field(None, description="Whether the repository should be private")
    description: Optional[str] = Field(None, description="Repository description")
    homepage: Optional[str] = Field(None, description="Repository homepage URL")
    has_issues: bool = Field(True, description="Enable issues for this repository")
    has_projects: bool = Field(True, description="Enable projects for this repository")
    has_wiki: bool = Field(True, description="Enable wiki for this repository")
    auto_init: bool = Field(False, description="Initialize with README")
    gitignore_template: Optional[str] = Field(None, description="Gitignore template to use")
    license_template: Optional[str] = Field(None, description="License template to use")
    allow_squash_merge: bool = Field(True, description="Allow squash merging")
    allow_merge_commit: bool = Field(True, description="Allow merge commits")
    allow_rebase_merge: bool = Field(True, description="Allow rebase merging")
    delete_branch_on_merge: bool = Field(False, description="Delete head branch after merge")

class SearchRepositoryConfig(BaseModel):
    """Configuration for searching repositories."""
    query: str = Field(..., description="Search query")
    sort: Optional[Literal["stars", "forks", "help-wanted-issues", "updated"]] = Field(None)
    order: Optional[Literal["asc", "desc"]] = Field(None, description="Sort order")
    page: Optional[int] = Field(None, description="Page number", ge=1)
    per_page: Optional[int] = Field(None, description="Results per page", ge=1, le=100)

class ForkRepositoryConfig(BaseModel):
    """Configuration for forking a repository."""
    organization: Optional[str] = Field(None, description="Organization to fork to")
    name: Optional[str] = Field(None, description="New name for the fork")
    default_branch_only: bool = Field(False, description="Fork only the default branch")

class RepositoryManager:
    """Manages GitHub repository operations."""
    
    def __init__(self, config: RepositoryConfig) -> None:
        """Initialize the repository manager.
        
        Args:
            config: Repository configuration including GitHub token
        """
        self.config = RepositoryConfig.model_validate(config)
        self.github = Github(self.config.token)
        
    async def create_repository(
        self,
        config: CreateRepositoryConfig,
    ) -> GithubRepository:
        """Create a new GitHub repository.
        
        Args:
            config: Repository creation configuration
            
        Returns:
            The created repository
        """
        # Validate config
        config = CreateRepositoryConfig.model_validate(config)
        
        # Set up parameters
        private = config.private if config.private is not None else self.config.private
        description = config.description if config.description is not None else NotSet
        homepage = config.homepage if config.homepage is not None else NotSet
        gitignore = config.gitignore_template if config.gitignore_template is not None else NotSet
        license_template = config.license_template if config.license_template is not None else NotSet
        
        user = self.github.get_user()
        return user.create_repo(
            name=config.name,
            private=private,
            description=description,
            homepage=homepage,
            has_issues=config.has_issues,
            has_projects=config.has_projects,
            has_wiki=config.has_wiki,
            auto_init=config.auto_init,
            gitignore_template=gitignore,
            license_template=license_template,
            allow_squash_merge=config.allow_squash_merge,
            allow_merge_commit=config.allow_merge_commit,
            allow_rebase_merge=config.allow_rebase_merge,
            delete_branch_on_merge=config.delete_branch_on_merge,
        )
    
    async def get_repository(
        self,
        owner: Optional[str] = None,
        name: Optional[str] = None,
    ) -> GithubRepository:
        """Get a GitHub repository by owner and name.
        
        Args:
            owner: Repository owner (defaults to config)
            name: Repository name (defaults to config)
            
        Returns:
            The requested repository
        """
        owner = owner or self.config.owner or self.github.get_user().login
        name = name or self.config.name
        
        if not owner or not name:
            raise ValueError("Repository owner and name must be provided")
            
        return self.github.get_repo(f"{owner}/{name}")
    
    async def search_repositories(
        self,
        config: SearchRepositoryConfig,
    ) -> List[GithubRepository]:
        """Search for GitHub repositories.
        
        Args:
            config: Search configuration
            
        Returns:
            List of matching repositories
        """
        # Validate config
        config = SearchRepositoryConfig.model_validate(config)
        
        # Set up parameters
        sort = config.sort if config.sort is not None else NotSet
        order = config.order if config.order is not None else NotSet
        
        # Get repositories with pagination
        repos = self.github.search_repositories(
            query=config.query,
            sort=sort,
            order=order,
        )
        
        # Apply pagination if specified
        if config.page is not None:
            repos = repos.get_page(config.page)
        elif config.per_page is not None:
            repos = list(repos)[:config.per_page]
        else:
            repos = list(repos)
        
        return repos
    
    async def fork_repository(
        self,
        repository: GithubRepository,
        config: Optional[ForkRepositoryConfig] = None,
    ) -> GithubRepository:
        """Fork a GitHub repository.
        
        Args:
            repository: Repository to fork
            config: Fork configuration
            
        Returns:
            The forked repository
        """
        if config:
            config = ForkRepositoryConfig.model_validate(config)
            organization = config.organization if config.organization is not None else NotSet
            name = config.name if config.name is not None else NotSet
            default_branch_only = config.default_branch_only
        else:
            organization = NotSet
            name = NotSet
            default_branch_only = False
        
        return repository.create_fork(
            organization=organization,
            name=name,
            default_branch_only=default_branch_only,
        )
    
    async def delete_repository(self, repository: GithubRepository) -> None:
        """Delete a GitHub repository.
        
        Args:
            repository: Repository to delete
        """
        repository.delete()
        
    def __enter__(self) -> 'RepositoryManager':
        return self
        
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.github.close()
        
    async def __aenter__(self) -> 'RepositoryManager':
        return self
        
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.github.close() 