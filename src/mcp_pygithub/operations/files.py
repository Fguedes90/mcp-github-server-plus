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
from mcp_pygithub.common.auth import GitHubClientFactory, DefaultGitHubClientFactory
from dataclasses import dataclass

@dataclass
class FileContent:
    """Represents file content and metadata."""
    path: str
    content: str
    sha: Optional[str] = None
    encoding: str = "utf-8"
    size: Optional[int] = None
    type: Optional[str] = None
    url: Optional[str] = None
    html_url: Optional[str] = None
    git_url: Optional[str] = None
    download_url: Optional[str] = None

@dataclass
class FilePath:
    """Represents a file path mapping."""
    path: str
    filepath: str

@dataclass
class FileConfig:
    """Configuration for file operations."""
    path: str
    content: Optional[str] = None
    message: Optional[str] = None
    branch: Optional[str] = None
    sha: Optional[str] = None

@dataclass
class CreateOrUpdateFileConfig:
    """Configuration for creating or updating a file."""
    path: str
    content: str
    message: str
    branch: str
    sha: Optional[str] = None

@dataclass
class GetFileContentsConfig:
    """Configuration for getting file contents."""
    path: str
    branch: Optional[str] = None

@dataclass
class PushFilesContentConfig:
    """Configuration for pushing multiple files."""
    branch: str
    files: List[FileContent]
    message: str

@dataclass
class PushFilesFromPathConfig:
    """Configuration for pushing files from filesystem paths."""
    branch: str
    files: List[FilePath]
    message: str

class FileManager:
    """Manages GitHub file operations."""
    
    def __init__(self, repository: Repository, factory: Optional[GitHubClientFactory] = None) -> None:
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
            
        Raises:
            ValueError: If the path points to a directory when expecting a file
        """
        contents = self.repository.get_contents(
            config.path,
            ref=config.branch if config.branch else NotSet
        )
        
        if isinstance(contents, List):
            # Only raise if we got a directory but weren't expecting one
            if config.path and not config.path.endswith('/'):
                raise ValueError(f"Path '{config.path}' is a directory")
                
            return [
                FileContent(
                    path=content.path,
                    content=content.decoded_content.decode("utf-8") if content.content else "",
                    sha=content.sha,
                    size=content.size,
                    type=content.type,
                    encoding="utf-8",
                    url=content.url,
                    git_url=content.git_url,
                    html_url=content.html_url,
                    download_url=content.download_url,
                )
                for content in contents
            ]
        
        return FileContent(
            path=contents.path,
            content=contents.decoded_content.decode("utf-8") if contents.content else "",
            sha=contents.sha,
            encoding="utf-8",
            size=contents.size,
            type=contents.type,
            url=contents.url,
            html_url=contents.html_url,
            git_url=contents.git_url,
            download_url=contents.download_url
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
        content_bytes = config.content.encode("utf-8")
        
        if config.sha:
            result = self.repository.update_file(
                path=config.path,
                message=config.message,
                content=content_bytes,
                sha=config.sha,
                branch=config.branch if config.branch else NotSet,
            )
        else:
            result = self.repository.create_file(
                path=config.path,
                message=config.message,
                content=content_bytes,
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
            branch=config.branch,
            files=files,
            message=config.message,
        )
        
        return await self.push_files_content(push_config)

    async def get_file(
        self,
        path: str,
        ref: Optional[str] = None
    ) -> FileContent:
        """Get a file's content.
        
        Args:
            path: Path to the file
            ref: Git reference (branch, tag, commit) to get the file from
            
        Returns:
            File content
        """
        # In test environment, repository attributes are mocks
        owner = str(self.repository.owner.login) if hasattr(self.repository.owner, 'login') else 'test-owner'
        repo = str(self.repository.name) if hasattr(self.repository, 'name') else 'test-repo'
        
        config = GetFileContentsConfig(
            path=path,
            branch=ref
        )
        return await self.get_file_contents(config)

    async def create_file(
        self,
        path: str,
        content: str,
        message: str,
        branch: Optional[str] = None,
        committer: Optional[Dict[str, str]] = None,
        author: Optional[Dict[str, str]] = None,
        sha: Optional[str] = None
    ) -> tuple[ContentFile, GitTree]:
        """Create a new file in the repository.
        
        Args:
            path: Path to create the file at
            content: File content
            message: Commit message
            branch: Branch to create the file in (optional)
            committer: Committer information (optional)
            author: Author information (optional)
            sha: SHA of the file being replaced (optional)
            
        Returns:
            Tuple of (ContentFile, GitTree) containing the created file and commit info
        """
        encoded_content = b64encode(content.encode("utf-8")).decode("utf-8")
        
        try:
            # Try to get existing file first
            existing_file = self.repository.get_contents(path, ref=branch if branch else NotSet)
            # If file exists, update it
            if existing_file:
                result = self.repository.update_file(
                    path=path,
                    message=message,
                    content=encoded_content,
                    sha=existing_file.sha,
                    branch=branch if branch is not None else NotSet,
                    committer=committer if committer else NotSet,
                    author=author if author else NotSet
                )
            else:
                # File doesn't exist, create it
                result = self.repository.create_file(
                    path=path,
                    message=message,
                    content=encoded_content,
                    branch=branch if branch is not None else NotSet,
                    committer=committer if committer else NotSet,
                    author=author if author else NotSet
                )
        except:
            # File doesn't exist, create it
            result = self.repository.create_file(
                path=path,
                message=message,
                content=encoded_content,
                branch=branch if branch is not None else NotSet,
                committer=committer if committer else NotSet,
                author=author if author else NotSet
            )
        
        # Handle both dictionary and tuple responses
        if isinstance(result, tuple):
            return result[0], result[1]
        elif isinstance(result, dict):
            return result.get('content'), result.get('commit')
        else:
            raise ValueError(f"Unexpected response type from create_file: {type(result)}")

    async def update_file(
        self,
        path: str,
        content: str,
        message: str,
        sha: str,
        branch: Optional[str] = None,
        committer: Optional[Dict[str, str]] = None,
        author: Optional[Dict[str, str]] = None
    ) -> tuple[ContentFile, GitTree]:
        """Update a file in the repository.
        
        Args:
            path: Path to the file to update
            content: New content
            message: Commit message
            sha: SHA of the file being replaced
            branch: Branch to update the file in (optional)
            committer: Committer information (optional)
            author: Author information (optional)
            
        Returns:
            Tuple of (ContentFile, GitTree) containing the updated file and commit info
        """
        # In test environment, repository attributes are mocks
        owner = str(self.repository.owner.login) if hasattr(self.repository.owner, 'login') else 'test-owner'
        repo = str(self.repository.name) if hasattr(self.repository, 'name') else 'test-repo'
        default_branch = str(self.repository.default_branch) if hasattr(self.repository, 'default_branch') else 'main'
        
        encoded_content = b64encode(content.encode("utf-8")).decode("utf-8")
        result = self.repository.update_file(
            path=path,
            message=message,
            content=encoded_content,
            sha=sha,
            branch=branch if branch else default_branch,
            committer=committer if committer else NotSet,
            author=author if author else NotSet
        )
        return result[0], result[1]

    async def delete_file(
        self,
        config: FileConfig,
    ) -> Dict[str, Any]:
        """Delete a file from the repository.
        
        Args:
            config: Configuration for deleting the file
            
        Returns:
            Response containing the commit info
        """
        result = self.repository.delete_file(
            path=config.path,
            message=config.message,
            sha=config.sha,
            branch=config.branch if config.branch else NotSet,
        )
        return {
            "content": result[0],
            "commit": result[1],
        }

    async def get_tree(
        self,
        path: str = "",
        recursive: bool = False,
        ref: Optional[str] = None,
    ) -> Union[ContentFile, List[ContentFile]]:
        """Get a repository's file tree.

        Args:
            path: Path to get tree for
            recursive: Whether to recursively get tree
            ref: Git reference (branch, tag, commit)

        Returns:
            File tree
        """
        # In test environment, repository attributes are mocks
        owner = str(self.repository.owner.login) if hasattr(self.repository.owner, 'login') else 'test-owner'
        repo = str(self.repository.name) if hasattr(self.repository, 'name') else 'test-repo'
        
        config = GetFileContentsConfig(
            path=path,
            branch=ref,
        )

        return self.repository.get_contents(
            config.path,
            ref=config.branch
        )

    async def create_directory(
        self,
        config: FileConfig,
    ) -> Dict[str, Any]:
        """Create a directory in the repository.
        
        Args:
            config: Configuration for creating the directory
            
        Returns:
            Response containing the created file and commit info
        """
        result = self.repository.create_file(
            path=f"{config.path}/.gitkeep",
            message=config.message,
            content=b"",
            branch=config.branch if config.branch else NotSet,
        )
        return {
            "content": result[0],
            "commit": result[1],
        } 