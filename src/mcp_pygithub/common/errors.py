"""Error classes for GitHub operations."""

class GitHubError(Exception):
    """Base class for GitHub errors."""
    pass

class NotFoundError(GitHubError):
    """Resource not found error."""
    pass

class UnauthorizedError(GitHubError):
    """Unauthorized access error."""
    pass

class ForbiddenError(GitHubError):
    """Forbidden access error."""
    pass

class ValidationError(GitHubError):
    """Validation error."""
    pass

class RateLimitError(GitHubError):
    """Rate limit exceeded error."""
    pass

class ServerError(GitHubError):
    """GitHub server error."""
    pass

class ConflictError(GitHubError):
    """Resource conflict error (e.g., merge conflicts)."""
    pass

class BadRequestError(GitHubError):
    """Bad request error (e.g., invalid parameters)."""
    pass

class TimeoutError(GitHubError):
    """Request timeout error."""
    pass

class NetworkError(GitHubError):
    """Network-related error."""
    pass

class ParseError(GitHubError):
    """Error parsing GitHub API response."""
    pass

class AuthenticationError(GitHubError):
    """Authentication-related error."""
    pass

class TwoFactorError(AuthenticationError):
    """Two-factor authentication required error."""
    pass

class ScopeError(AuthenticationError):
    """Insufficient token scope error."""
    pass

class SearchError(GitHubError):
    """Search operation error."""
    pass

class RepositoryError(GitHubError):
    """Repository operation error."""
    pass 