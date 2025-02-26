"""File management tools for GitHub MCP server."""

from typing import List, Optional
from pydantic import BaseModel, Field

from mcp.types import Tool
from .common import (
    BaseInput, GitRefInput,
    CommitSha,
    sha_field, path_field, string_field
)

class GetFileInput(GitRefInput):
    """Input schema for get_file tool."""
    path: str = path_field(
        description="File path in repository",
        json_schema_extra={"examples": ["src/main.py"]},
        validation_alias="path"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "path": "src/main.py",
                    "ref": "main"
                }
            ]
        }
    }

class CreateFileInput(BaseInput):
    """Input schema for create_file tool."""
    path: str = path_field(
        description="File path in repository",
        json_schema_extra={"examples": ["docs/README.md"]},
        validation_alias="path"
    )
    content: str = string_field(
        description="File content",
        json_schema_extra={"examples": ["# New File\n\nThis is a new file."]},
        validation_alias="content"
    )
    message: str = string_field(
        description="Commit message",
        json_schema_extra={"examples": ["Create new file"]},
        validation_alias="message"
    )
    branch: Optional[str] = string_field(
        description="Branch to create file in",
        json_schema_extra={"examples": ["feature/new-docs"]},
        validation_alias="branch",
        default=None
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "path": "docs/README.md",
                    "content": "# New File\n\nThis is a new file.",
                    "message": "Create new file",
                    "branch": "feature/new-docs"
                }
            ]
        }
    }

class UpdateFileInput(BaseInput):
    """Input schema for update_file tool."""
    path: str = path_field(
        description="File path in repository",
        json_schema_extra={"examples": ["src/main.py"]},
        validation_alias="path"
    )
    content: str = string_field(
        description="New file content",
        json_schema_extra={"examples": ["Updated content"]},
        validation_alias="content"
    )
    message: str = string_field(
        description="Commit message",
        json_schema_extra={"examples": ["Update file content"]},
        validation_alias="message"
    )
    sha: CommitSha = sha_field(
        description="Current file SHA",
        json_schema_extra={"examples": ["abc123..."]},
        validation_alias="sha",
        min_length=40,
        max_length=40
    )
    branch: Optional[str] = string_field(
        description="Branch to update file in",
        json_schema_extra={"examples": ["feature/update"]},
        validation_alias="branch",
        default=None
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "path": "src/main.py",
                    "content": "Updated content",
                    "message": "Update file content",
                    "sha": "abc123def456...",
                    "branch": "feature/update"
                }
            ]
        }
    }

class DeleteFileInput(BaseInput):
    """Input schema for delete_file tool."""
    path: str = path_field(
        description="File path in repository",
        json_schema_extra={"examples": ["old/file.txt"]},
        validation_alias="path"
    )
    message: str = string_field(
        description="Commit message",
        json_schema_extra={"examples": ["Delete old file"]},
        validation_alias="message"
    )
    sha: CommitSha = sha_field(
        description="Current file SHA",
        json_schema_extra={"examples": ["abc123..."]},
        validation_alias="sha",
        min_length=40,
        max_length=40
    )
    branch: Optional[str] = string_field(
        description="Branch to delete file from",
        json_schema_extra={"examples": ["feature/cleanup"]},
        validation_alias="branch",
        default=None
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "path": "old/file.txt",
                    "message": "Delete old file",
                    "sha": "abc123def456...",
                    "branch": "feature/cleanup"
                }
            ]
        }
    }

def files_tools() -> List[Tool]:
    """Get file-related tools."""
    return [
        Tool(
            name="get_file",
            description="""Get file contents from repository.
            
            Retrieves the contents of a file at a specified path. Can optionally
            specify a Git reference (branch, tag, commit) to get file from.
            """,
            inputSchema=GetFileInput.model_json_schema()
        ),
        Tool(
            name="create_file",
            description="""Create a new file in repository.
            
            Creates a new file with specified content. Requires a commit message
            and can optionally specify a branch to create the file in.
            """,
            inputSchema=CreateFileInput.model_json_schema()
        ),
        Tool(
            name="update_file",
            description="""Update an existing file in repository.
            
            Updates file content. Requires current file SHA and commit message.
            Can optionally specify a branch to update the file in.
            """,
            inputSchema=UpdateFileInput.model_json_schema()
        ),
        Tool(
            name="delete_file",
            description="""Delete a file from repository.
            
            Deletes a file. Requires current file SHA and commit message.
            Can optionally specify a branch to delete the file from.
            """,
            inputSchema=DeleteFileInput.model_json_schema()
        )
    ] 