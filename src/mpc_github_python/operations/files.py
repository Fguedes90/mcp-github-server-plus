"""Files module for GitHub file operations.

This module provides functionality for:
- Reading file contents
- Writing/updating files
- Getting file metadata
- Managing file trees and references
"""

from typing import List, Optional, Dict, Any, Union
from base64 import b64encode, b64decode
from pathlib import Path
from pydantic import BaseModel, Field
from github.Repository import Repository
from github.ContentFile import ContentFile
from github.GitTree import GitTree
from github.GithubObject import NotSet

class FileContent(BaseModel):
    """Represents file content and metadata."""
    path: str = Field(..., description="Path to the file in the repository")
    content: str = Field(..., description="Content of the file")

class FilePath(BaseModel):
    """Represents a file path mapping."""
    path: str = Field(..., description="Path in the repository")
    filepath: str = Field(..., description="Path on the local filesystem")

class CreateOrUpdateFileConfig(BaseModel):
    """Configuration for creating or updating a file."""
    owner: str = Field(..., description="Repository owner (username or organization)")
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="Path where to create/update the file")
    content: str = Field(..., description="Content of the file")
    message: str = Field(..., description="Commit message")
    branch: str = Field(..., description="Branch to create/update the file in")
    sha: Optional[str] = Field(None, description="SHA of the file being replaced (required when updating existing files)")

class GetFileContentsConfig(BaseModel):
    """Configuration for getting file contents."""
    owner: str = Field(..., description="Repository owner (username or organization)")
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="Path to the file or directory")
    branch: Optional[str] = Field(None, description="Branch to get contents from")

class PushFilesContentConfig(BaseModel):
    """Configuration for pushing multiple files."""
    owner: str = Field(..., description="Repository owner (username or organization)")
    repo: str = Field(..., description="Repository name")
    branch: str = Field(..., description="Branch to push to (e.g., 'main' or 'master')")
    files: List[FileContent] = Field(..., description="Array of files to push with their content")
    message: str = Field(..., description="Commit message")

class PushFilesFromPathConfig(BaseModel):
    """Configuration for pushing files from filesystem paths."""
    owner: str = Field(..., description="Repository owner (username or organization)")
    repo: str = Field(..., description="Repository name")
    branch: str = Field(..., description="Branch to push to (e.g., 'main' or 'master')")
    files: List[FilePath] = Field(..., description="Array of files to push from filesystem paths")
    message: str = Field(..., description="Commit message")

class FileManager:
    """Manages GitHub file operations."""
    
    def __init__(self, repository: Repository) -> None:
        """Initialize the file manager.
        
        Args:
            repository: GitHub repository to operate on
        """
        self.repository = repository
    
    async def get_file_contents(
        self,
        config: GetFileContentsConfig,
    ) -> Union[FileContent, List[FileContent]]:
        """Get a file's content and metadata.
        
        Args:
            config: Configuration for getting file contents
            
        Returns:
            File content and metadata or list of contents for directories
        """
        contents = self.repository.get_contents(
            config.path,
            ref=config.branch if config.branch else NotSet
        )
        
        if isinstance(contents, List):
            return [
                FileContent(
                    path=content.path,
                    content=b64decode(content.content).decode(content.encoding or "utf-8")
                    if content.content else ""
                )
                for content in contents
                if content.type == "file"
            ]
        
        return FileContent(
            path=contents.path,
            content=b64decode(contents.content).decode(contents.encoding or "utf-8")
            if contents.content else ""
        )
    
    async def create_or_update_file(
        self,
        config: CreateOrUpdateFileConfig,
    ) -> Dict[str, Any]:
        """Create or update a file in the repository.
        
        Args:
            config: Configuration for creating/updating the file
            
        Returns:
            Response containing the created/updated file and commit info
        """
        encoded_content = b64encode(config.content.encode("utf-8")).decode("utf-8")
        
        if config.sha:
            result = self.repository.update_file(
                path=config.path,
                message=config.message,
                content=encoded_content,
                sha=config.sha,
                branch=config.branch if config.branch else NotSet,
            )
        else:
            result = self.repository.create_file(
                path=config.path,
                message=config.message,
                content=encoded_content,
                branch=config.branch if config.branch else NotSet,
            )
            
        return {
            "content": result[0],
            "commit": result[1],
        }
    
    async def create_tree(
        self,
        files: List[FileContent],
        base_tree: Optional[str] = None,
    ) -> GitTree:
        """Create a Git tree from a list of files.
        
        Args:
            files: List of files to include in the tree
            base_tree: Optional base tree SHA
            
        Returns:
            Created Git tree
        """
        tree_elements = [
            {
                "path": file.path,
                "mode": "100644",
                "type": "blob",
                "content": file.content,
            }
            for file in files
        ]
        
        return self.repository.create_git_tree(
            tree_elements,
            base_tree=base_tree if base_tree else NotSet
        )
    
    async def create_commit(
        self,
        message: str,
        tree: str,
        parents: List[str],
    ) -> Dict[str, Any]:
        """Create a Git commit.
        
        Args:
            message: Commit message
            tree: Tree SHA
            parents: List of parent commit SHAs
            
        Returns:
            Created commit information
        """
        commit = self.repository.create_git_commit(
            message=message,
            tree=tree,
            parents=parents,
        )
        return {
            "sha": commit.sha,
            "message": commit.message,
            "tree": {"sha": commit.tree.sha},
            "parents": [{"sha": p.sha} for p in commit.parents],
        }
    
    async def update_reference(
        self,
        ref: str,
        sha: str,
        force: bool = True,
    ) -> Dict[str, Any]:
        """Update a Git reference.
        
        Args:
            ref: Reference to update (e.g., 'heads/main')
            sha: Target commit SHA
            force: Whether to force update
            
        Returns:
            Updated reference information
        """
        git_ref = self.repository.get_git_ref(ref)
        git_ref.edit(sha=sha, force=force)
        return {
            "ref": git_ref.ref,
            "object": {"sha": git_ref.object.sha},
        }
    
    async def push_files_content(
        self,
        config: PushFilesContentConfig,
    ) -> Dict[str, Any]:
        """Push multiple files to the repository in a single commit.
        
        Args:
            config: Configuration for pushing files
            
        Returns:
            Updated reference information
        """
        ref = self.repository.get_git_ref(f"heads/{config.branch}")
        commit_sha = ref.object.sha
        
        tree = await self.create_tree(config.files, commit_sha)
        commit = await self.create_commit(config.message, tree.sha, [commit_sha])
        return await self.update_reference(f"heads/{config.branch}", commit["sha"])
    
    async def push_files_from_path(
        self,
        config: PushFilesFromPathConfig,
    ) -> Dict[str, Any]:
        """Push files from filesystem paths to the repository.
        
        Args:
            config: Configuration for pushing files
            
        Returns:
            Updated reference information
        """
        files = []
        for file_path in config.files:
            path = Path(file_path.filepath)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path.filepath}")
                
            content = path.read_text(encoding="utf-8")
            files.append(FileContent(path=file_path.path, content=content))
        
        push_config = PushFilesContentConfig(
            owner=config.owner,
            repo=config.repo,
            branch=config.branch,
            files=files,
            message=config.message,
        )
        
        return await self.push_files_content(push_config) 