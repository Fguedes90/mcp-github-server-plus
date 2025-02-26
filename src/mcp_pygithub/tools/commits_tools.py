"""Commit management tools for GitHub MCP server."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from mcp.types import Tool
from .common import (
    BaseInput, GitRefInput, DateRangeInput, PersonInfo,
    CommitSha, TreeSha, GitRef,
    sha_field, path_field, string_field, list_field
)

class GetCommitInput(BaseInput):
    """Input schema for get_commit tool."""
    sha: CommitSha = sha_field(
        description="Commit SHA",
        json_schema_extra={"examples": ["abc123def456..."]},
        validation_alias="sha"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "sha": "abc123def456..."
                }
            ]
        }
    }

class ListCommitsInput(GitRefInput, DateRangeInput):
    """Input schema for list_commits tool."""
    sha: Optional[GitRef] = string_field(
        description="SHA or branch to start listing commits from",
        json_schema_extra={"examples": ["main"]},
        validation_alias="sha",
        default=None
    )
    path: Optional[str] = path_field(
        description="Only commits containing this file path",
        json_schema_extra={"examples": ["src/main.py"]},
        validation_alias="path",
        default=None
    )
    author: Optional[str] = string_field(
        description="GitHub username of author",
        json_schema_extra={"examples": ["octocat"]},
        validation_alias="author",
        default=None
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "sha": "main",
                    "path": "src/main.py",
                    "author": "octocat",
                    "since": "2024-01-01T00:00:00Z",
                    "until": "2024-02-29T23:59:59Z"
                }
            ]
        }
    }

class CompareCommitsInput(BaseInput):
    """Input schema for compare_commits tool."""
    base: GitRef = string_field(
        description="Base commit SHA or branch name",
        json_schema_extra={"examples": ["main"]},
        validation_alias="base"
    )
    head: GitRef = string_field(
        description="Head commit SHA or branch name",
        json_schema_extra={"examples": ["feature/new-feature"]},
        validation_alias="head"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "base": "main",
                    "head": "feature/new-feature"
                }
            ]
        }
    }

class CreateCommitInput(BaseInput):
    """Input schema for create_commit tool."""
    message: str = string_field(
        description="Commit message",
        json_schema_extra={"examples": ["Add new feature\n\nDetailed description here"]},
        validation_alias="message"
    )
    tree: TreeSha = sha_field(
        description="SHA of the tree object",
        json_schema_extra={"examples": ["abc123def456..."]},
        validation_alias="tree",
        min_length=40,
        max_length=40
    )
    parents: List[CommitSha] = list_field(
        description="List of parent commit SHAs",
        json_schema_extra={"examples": [["def456abc123..."]]},
        validation_alias="parents"
    )
    author: Optional[PersonInfo] = Field(
        default=None,
        description="Author information"
    )
    committer: Optional[PersonInfo] = Field(
        default=None,
        description="Committer information"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Add new feature\n\nDetailed description here",
                    "tree": "abc123def456...",
                    "parents": ["def456abc123..."],
                    "author": {
                        "name": "John Doe",
                        "email": "john@example.com",
                        "date": "2024-02-29T12:00:00Z"
                    }
                }
            ]
        }
    }

def commits_tools() -> List[Tool]:
    """Get commit-related tools."""
    return [
        Tool(
            name="get_commit",
            description="""Get a specific commit.
            
            Retrieves detailed information about a commit identified by its SHA.
            """,
            inputSchema=GetCommitInput.model_json_schema()
        ),
        Tool(
            name="list_commits",
            description="""List repository commits.
            
            Retrieves a list of commits. Can be filtered by author, date range,
            and file path.
            """,
            inputSchema=ListCommitsInput.model_json_schema()
        ),
        Tool(
            name="compare_commits",
            description="""Compare two commits.
            
            Shows the difference between two commits or branches, including
            changed files and commit history.
            """,
            inputSchema=CompareCommitsInput.model_json_schema()
        ),
        Tool(
            name="create_commit",
            description="""Create a new commit.
            
            Creates a new Git commit object. Requires the tree SHA and parent
            commit SHAs. Can specify custom author and committer information.
            """,
            inputSchema=CreateCommitInput.model_json_schema()
        )
    ] 