"""GitHub handler for MPC."""

from typing import Any, Dict, List, Optional
from mcp.handlers import BaseHandler
from ..operations import (
    ActionManager,
    CommitManager,
    FileManager,
    IssueManager,
    PullManager,
    RepositoryManager,
    SearchManager,
)

class GitHubHandler(BaseHandler):
    """GitHub handler for MPC."""
    
    def __init__(self, token: Optional[str] = None) -> None:
        """Initialize the handler.
        
        Args:
            token: GitHub token
        """
        super().__init__()
        self.token = token
        self.repository: Optional[RepositoryManager] = None
        self.files: Optional[FileManager] = None
        self.issues: Optional[IssueManager] = None
        self.pulls: Optional[PullManager] = None
        self.commits: Optional[CommitManager] = None
        self.actions: Optional[ActionManager] = None
        self.search: Optional[SearchManager] = None
    
    async def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize the handler with context.
        
        Args:
            context: Handler context
        """
        # Get repository information from context
        owner = context.get("owner")
        name = context.get("name")
        
        # Create repository manager
        self.repository = RepositoryManager(token=self.token, owner=owner, name=name)
        repo = await self.repository.get_repository()
        
        # Initialize other managers
        self.files = FileManager(repo)
        self.issues = IssueManager(repo)
        self.pulls = PullManager(repo)
        self.commits = CommitManager(repo)
        self.actions = ActionManager(repo)
        self.search = SearchManager(repo)
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MPC request.
        
        Args:
            request: MPC request
            
        Returns:
            MPC response
        """
        # Get request details
        action = request.get("action")
        params = request.get("params", {})
        
        # Handle repository operations
        if action.startswith("repository."):
            return await self._handle_repository(action, params)
        
        # Handle file operations
        if action.startswith("files."):
            return await self._handle_files(action, params)
        
        # Handle issue operations
        if action.startswith("issues."):
            return await self._handle_issues(action, params)
        
        # Handle pull request operations
        if action.startswith("pulls."):
            return await self._handle_pulls(action, params)
        
        # Handle commit operations
        if action.startswith("commits."):
            return await self._handle_commits(action, params)
        
        # Handle action operations
        if action.startswith("actions."):
            return await self._handle_actions(action, params)
        
        # Handle search operations
        if action.startswith("search."):
            return await self._handle_search(action, params)
        
        raise ValueError(f"Unknown action: {action}")
    
    async def _handle_repository(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle repository operations."""
        if not self.repository:
            raise ValueError("Repository manager not initialized")
        
        method = action.split(".")[1]
        handler = getattr(self.repository, method, None)
        if not handler:
            raise ValueError(f"Unknown repository method: {method}")
        
        result = await handler(**params)
        return {"result": result}
    
    async def _handle_files(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file operations."""
        if not self.files:
            raise ValueError("File manager not initialized")
        
        method = action.split(".")[1]
        handler = getattr(self.files, method, None)
        if not handler:
            raise ValueError(f"Unknown file method: {method}")
        
        result = await handler(**params)
        return {"result": result}
    
    async def _handle_issues(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue operations."""
        if not self.issues:
            raise ValueError("Issue manager not initialized")
        
        method = action.split(".")[1]
        handler = getattr(self.issues, method, None)
        if not handler:
            raise ValueError(f"Unknown issue method: {method}")
        
        result = await handler(**params)
        return {"result": result}
    
    async def _handle_pulls(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request operations."""
        if not self.pulls:
            raise ValueError("Pull request manager not initialized")
        
        method = action.split(".")[1]
        handler = getattr(self.pulls, method, None)
        if not handler:
            raise ValueError(f"Unknown pull request method: {method}")
        
        result = await handler(**params)
        return {"result": result}
    
    async def _handle_commits(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle commit operations."""
        if not self.commits:
            raise ValueError("Commit manager not initialized")
        
        method = action.split(".")[1]
        handler = getattr(self.commits, method, None)
        if not handler:
            raise ValueError(f"Unknown commit method: {method}")
        
        result = await handler(**params)
        return {"result": result}
    
    async def _handle_actions(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle action operations."""
        if not self.actions:
            raise ValueError("Action manager not initialized")
        
        method = action.split(".")[1]
        handler = getattr(self.actions, method, None)
        if not handler:
            raise ValueError(f"Unknown action method: {method}")
        
        result = await handler(**params)
        return {"result": result}
    
    async def _handle_search(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search operations."""
        if not self.search:
            raise ValueError("Search manager not initialized")
        
        method = action.split(".")[1]
        handler = getattr(self.search, method, None)
        if not handler:
            raise ValueError(f"Unknown search method: {method}")
        
        result = await handler(**params)
        return {"result": result} 