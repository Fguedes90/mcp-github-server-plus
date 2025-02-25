"""Branches module for GitHub branch operations.

This module provides functionality for:
- Branch creation and deletion
- Branch protection rules
- Branch listing and management
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from github.Repository import Repository as GithubRepository
from github.Branch import Branch as GithubBranch
from github.BranchProtection import BranchProtection
from github.GithubObject import NotSet

class BranchConfig(BaseModel):
    """Configuration for branch operations."""
    name: str = Field(..., description="Name for the new branch")
    source_branch: Optional[str] = Field(None, description="Source branch to create from")

class BranchProtectionConfig(BaseModel):
    """Configuration for branch protection rules."""
    required_status_checks: Optional[List[str]] = None
    enforce_admins: bool = False
    required_pull_request_reviews: bool = False
    required_approving_review_count: Optional[int] = None
    dismiss_stale_reviews: bool = False
    require_code_owner_reviews: bool = False
    restrictions: Optional[Dict[str, List[str]]] = None

class BranchManager:
    """Manages GitHub branch operations."""
    
    def __init__(self, repository: GithubRepository) -> None:
        """Initialize the branch manager.
        
        Args:
            repository: GitHub repository to operate on
        """
        self.repository = repository
    
    async def get_branch(self, branch: str) -> GithubBranch:
        """Get a branch by name.
        
        Args:
            branch: Branch name
            
        Returns:
            The requested branch
        """
        try:
            return self.repository.get_branch(branch)
        except Exception as e:
            if "Branch not found" in str(e):
                # Create initial commit if repository is empty
                if not list(self.repository.get_commits()):
                    self.repository.create_file(
                        path="README.md",
                        message="Initial commit",
                        content="# Repository\nInitialized by BranchManager",
                        branch=self.repository.default_branch,
                    )
                    return self.repository.get_branch(branch)
            raise
    
    async def get_branch_sha(self, branch: str) -> str:
        """Get the SHA of a branch.
        
        Args:
            branch: Branch name
            
        Returns:
            The branch's SHA
        """
        branch_obj = await self.get_branch(branch)
        return branch_obj.commit.sha
    
    async def get_default_branch_sha(self) -> str:
        """Get the SHA of the default branch.
        
        Returns:
            The default branch's SHA
        """
        return await self.get_branch_sha(self.repository.default_branch)
    
    async def create_branch(
        self,
        config: BranchConfig,
    ) -> GithubBranch:
        """Create a new branch.
        
        Args:
            config: Branch configuration
            
        Returns:
            The created branch
        """
        # Validate config
        config = BranchConfig.model_validate(config)
        
        # Get source branch (default branch if not specified)
        source = config.source_branch or self.repository.default_branch
        source_sha = await self.get_branch_sha(source)
        
        # Create new branch from source
        ref = self.repository.create_git_ref(
            ref=f"refs/heads/{config.name}",
            sha=source_sha
        )
        
        return await self.get_branch(config.name)
    
    async def update_branch(
        self,
        branch: str,
        sha: str,
        force: bool = False,
    ) -> GithubBranch:
        """Update a branch to point to a new commit.
        
        Args:
            branch: Branch name to update
            sha: New commit SHA
            force: Whether to force update
            
        Returns:
            The updated branch
        """
        ref = self.repository.get_git_ref(f"heads/{branch}")
        ref.edit(sha=sha, force=force)
        return await self.get_branch(branch)
    
    async def delete_branch(self, branch: str) -> None:
        """Delete a branch.
        
        Args:
            branch: Branch name to delete
        """
        ref = self.repository.get_git_ref(f"heads/{branch}")
        ref.delete()
    
    async def protect_branch(
        self,
        branch: str,
        config: BranchProtectionConfig,
    ) -> BranchProtection:
        """Add protection rules to a branch.
        
        Args:
            branch: Branch name to protect
            config: Protection rule configuration
            
        Returns:
            The branch protection object
        """
        # Validate config
        config = BranchProtectionConfig.model_validate(config)
        
        branch_obj = await self.get_branch(branch)
        
        # Configure required status checks
        required_status_checks = {
            "strict": True,
            "contexts": config.required_status_checks or [],
        } if config.required_status_checks else NotSet
        
        # Configure required reviews
        review_count = config.required_approving_review_count or 1
        dismiss_stale = config.dismiss_stale_reviews
        require_code_owner = config.require_code_owner_reviews
        
        # Configure restrictions
        restrictions = config.restrictions or NotSet
        
        return branch_obj.edit_protection(
            strict=True,
            contexts=config.required_status_checks or [],
            enforce_admins=config.enforce_admins,
            user_push_restrictions=restrictions.get("users", []) if restrictions != NotSet else NotSet,
            team_push_restrictions=restrictions.get("teams", []) if restrictions != NotSet else NotSet,
            require_code_owner_reviews=require_code_owner,
            required_approving_review_count=review_count,
            dismiss_stale_reviews=dismiss_stale,
        )
    
    async def remove_protection(self, branch: str) -> None:
        """Remove protection rules from a branch.
        
        Args:
            branch: Branch name to unprotect
        """
        branch_obj = await self.get_branch(branch)
        branch_obj.remove_protection()
    
    async def list_branches(self) -> List[GithubBranch]:
        """List all branches in the repository.
        
        Returns:
            List of branches
        """
        return list(self.repository.get_branches()) 