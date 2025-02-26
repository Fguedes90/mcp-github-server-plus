"""Authentication module for GitHub operations.

This module provides centralized authentication functionality for GitHub API access.
It handles token management and client initialization in a consistent way using dependency injection.
"""

from typing import Optional, Dict, Type, Protocol
from github import Github

class GitHubClientFactory(Protocol):
    """Protocol defining the interface for GitHub client factories."""
    def create_client(self, token: str) -> Github:
        """Create a new GitHub client instance."""
        ...
    
    def clear_cache(self) -> None:
        """Clear any cached client instances."""
        ...

class DefaultGitHubClientFactory:
    """Default implementation of GitHubClientFactory using a singleton pattern."""
    
    def __init__(self, github_class: Type[Github] = Github):
        """Initialize the factory.
        
        Args:
            github_class: The GitHub client class to use (for testing)
        """
        self._github_class = github_class
        self._clients: Dict[str, Github] = {}
    
    def create_client(self, token: str) -> Github:
        """Create a GitHub client."""
        if token not in self._clients:
            self._clients[token] = self._github_class(login_or_token=token)
        return self._clients[token]
    
    def clear_cache(self) -> None:
        """Clear the client cache."""
        self._clients.clear()

# Global factory instance
_default_factory = DefaultGitHubClientFactory()

def create_github_client(token: str, factory: Optional[GitHubClientFactory] = None) -> Github:
    """Create a GitHub client instance using the provided factory.
    
    Args:
        token: GitHub personal access token
        factory: Optional factory to use for client creation
        
    Returns:
        Authenticated GitHub client instance
    """
    factory = factory or _default_factory
    return factory.create_client(token)

def validate_token(token: str, factory: Optional[GitHubClientFactory] = None) -> bool:
    """Validate a GitHub token by attempting to make a simple API call.
    
    Args:
        token: GitHub personal access token to validate
        factory: Optional factory to use for client creation
        
    Returns:
        True if the token is valid, False otherwise
    """
    try:
        client = create_github_client(token, factory)
        # Try to get the authenticated user
        client.get_user().login
        return True
    except Exception:
        return False

def clear_github_clients(factory: Optional[GitHubClientFactory] = None) -> None:
    """Clear the GitHub client cache.
    
    Args:
        factory: Optional factory to clear cache for
    """
    factory = factory or _default_factory
    factory.clear_cache() 