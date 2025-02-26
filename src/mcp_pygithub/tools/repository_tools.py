"""Repository tools for GitHub MCP server."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from mcp.types import Tool

class GetRepositoryInput(BaseModel):
    """Input schema for get_repository tool."""
    owner: str = Field(
        description="Repository owner",
        validate_default=True,
        pre=True,
        json_schema_extra={"examples": ["octocat"]},
        validation_alias="owner",
        strict=True,
        min_length=1
    )
    name: str = Field(
        description="Repository name",
        validate_default=True,
        pre=True,
        json_schema_extra={"examples": ["Hello-World"]},
        validation_alias="name",
        strict=True,
        min_length=1,
        pattern=r"^[^/]+$"  # Não pode conter /
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "owner": "octocat",
                    "name": "Hello-World"
                }
            ]
        }
    }

class CreateRepositoryInput(BaseModel):
    """Input schema for create_repository tool."""
    name: str = Field(
        description="Repository name",
        validate_default=True,
        pre=True,
        json_schema_extra={"examples": ["my-new-repo"]},
        validation_alias="name",
        strict=True,
        min_length=1,
        max_length=100,
        pattern=r"^[^/]+$"  # Não pode conter /
    )
    private: bool = Field(
        default=False,
        description="Whether the repository is private"
    )
    description: Optional[str] = Field(
        default=None,
        description="Repository description"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "my-new-repo",
                    "private": True,
                    "description": "A new repository created via MCP"
                }
            ]
        }
    }

class DeleteRepositoryInput(BaseModel):
    """Input schema for delete_repository tool."""
    name: str = Field(
        description="Repository name",
        validate_default=True,
        pre=True,
        json_schema_extra={"examples": ["repo-to-delete"]},
        validation_alias="name",
        strict=True,
        min_length=1,
        pattern=r"^[^/]+$"  # Não pode conter /
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "repo-to-delete"
                }
            ]
        }
    }

class SetRepositoryInput(BaseModel):
    """Input schema for set_repository tool."""
    owner: str = Field(
        description="Repository owner",
        validate_default=True,
        pre=True,
        json_schema_extra={"examples": ["octocat"]},
        validation_alias="owner",
        strict=True,
        min_length=1
    )
    name: str = Field(
        description="Repository name",
        validate_default=True,
        pre=True,
        json_schema_extra={"examples": ["Hello-World"]},
        validation_alias="name",
        strict=True,
        min_length=1,
        pattern=r"^[^/]+$"  # Não pode conter /
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "owner": "octocat",
                    "name": "Hello-World"
                }
            ]
        }
    }

def repository_tools() -> List[Tool]:
    """Get repository-related tools."""
    return [
        Tool(
            name="get_repository",
            description="""Get a repository by owner and name.
            
            Retrieves information about a GitHub repository using the owner's username
            and repository name.
            """,
            inputSchema=GetRepositoryInput.model_json_schema()
        ),
        Tool(
            name="create_repository",
            description="""Create a new GitHub repository.
            
            Creates a new repository under the authenticated user's account.
            The repository can be public or private, and an optional description
            can be provided.
            """,
            inputSchema=CreateRepositoryInput.model_json_schema()
        ),
        Tool(
            name="delete_repository",
            description="""Delete a GitHub repository.
            
            Permanently deletes a repository. This action cannot be undone!
            Make sure you have the necessary permissions to delete the repository.
            """,
            inputSchema=DeleteRepositoryInput.model_json_schema()
        ),
        Tool(
            name="set_repository",
            description="""Set the current repository context.
            
            Changes the current working repository context for subsequent operations.
            This affects all repository-related operations that follow.
            """,
            inputSchema=SetRepositoryInput.model_json_schema()
        )
    ] 