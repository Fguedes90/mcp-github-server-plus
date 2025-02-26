"""Pull request management tools for GitHub MCP server."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from mcp.types import Tool
from .common import (
    BaseInput, SortableInput, GitRefInput,
    string_field
)

class ListPullRequestsInput(SortableInput):
    """Input schema for list_pull_requests tool."""
    state: Optional[Literal["open", "closed", "all"]] = Field(
        default="open",
        description="State of pull requests to list"
    )
    base: Optional[str] = string_field(
        description="Filter by base branch name",
        json_schema_extra={"examples": ["main"]},
        validation_alias="base",
        default=None
    )
    sort: Optional[Literal["created", "updated", "popularity", "long-running"]] = Field(
        default="created",
        description="What to sort results by"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "state": "open",
                    "base": "main",
                    "sort": "updated",
                    "direction": "desc"
                }
            ]
        }
    }

class CreatePullRequestInput(BaseInput):
    """Input schema for create_pull_request tool."""
    title: str = string_field(
        description="Pull request title",
        json_schema_extra={"examples": ["Add new feature"]},
        validation_alias="title",
        max_length=256
    )
    body: Optional[str] = string_field(
        description="Pull request description in markdown",
        json_schema_extra={"examples": ["This PR adds a new login feature"]},
        validation_alias="body",
        default=None
    )
    head: str = string_field(
        description="Name of branch where changes are implemented",
        json_schema_extra={"examples": ["feature/new-login"]},
        validation_alias="head"
    )
    base: str = string_field(
        description="Name of branch you want changes pulled into",
        json_schema_extra={"examples": ["main"]},
        validation_alias="base"
    )
    draft: Optional[bool] = Field(
        default=False,
        description="Whether to create the pull request as a draft"
    )
    maintainer_can_modify: Optional[bool] = Field(
        default=True,
        description="Whether maintainers can modify the pull request"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Add new feature",
                    "body": "This PR adds a new login feature",
                    "head": "feature/new-login",
                    "base": "main",
                    "draft": False,
                    "maintainer_can_modify": True
                }
            ]
        }
    }

class UpdatePullRequestInput(BaseInput):
    """Input schema for update_pull_request tool."""
    number: int = Field(
        description="Pull request number",
        validate_default=True,
        pre=True,
        json_schema_extra={"examples": [42]},
        validation_alias="number",
        strict=True,
        gt=0
    )
    title: Optional[str] = string_field(
        description="New pull request title",
        json_schema_extra={"examples": ["Updated: Add new feature"]},
        validation_alias="title",
        max_length=256,
        default=None
    )
    body: Optional[str] = string_field(
        description="New pull request description in markdown",
        json_schema_extra={"examples": ["Updated description of the new feature"]},
        validation_alias="body",
        default=None
    )
    state: Optional[Literal["open", "closed"]] = Field(
        default=None,
        description="State of the pull request"
    )
    base: Optional[str] = string_field(
        description="Name of branch you want changes pulled into",
        json_schema_extra={"examples": ["develop"]},
        validation_alias="base",
        default=None
    )
    maintainer_can_modify: Optional[bool] = Field(
        default=None,
        description="Whether maintainers can modify the pull request"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "number": 42,
                    "title": "Updated: Add new feature",
                    "body": "Updated description of the new feature",
                    "state": "open",
                    "base": "develop",
                    "maintainer_can_modify": True
                }
            ]
        }
    }

class MergePullRequestInput(BaseInput):
    """Input schema for merge_pull_request tool."""
    number: int = Field(
        description="Pull request number",
        validate_default=True,
        pre=True,
        json_schema_extra={"examples": [42]},
        validation_alias="number",
        strict=True,
        gt=0
    )
    merge_method: Optional[Literal["merge", "squash", "rebase"]] = Field(
        default="merge",
        description="Method to use for merging"
    )
    commit_title: Optional[str] = string_field(
        description="Title for the merge commit",
        json_schema_extra={"examples": ["Merge pull request #42"]},
        validation_alias="commit_title",
        max_length=256,
        default=None
    )
    commit_message: Optional[str] = string_field(
        description="Message for the merge commit",
        json_schema_extra={"examples": ["Merging new login feature"]},
        validation_alias="commit_message",
        default=None
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "number": 42,
                    "merge_method": "squash",
                    "commit_title": "Merge pull request #42",
                    "commit_message": "Merging new login feature"
                }
            ]
        }
    }

def pulls_tools() -> List[Tool]:
    """Get pull request-related tools."""
    return [
        Tool(
            name="list_pull_requests",
            description="""List repository pull requests.
            
            Retrieves a list of pull requests. Can be filtered by state and base branch.
            Supports sorting by various criteria.
            """,
            inputSchema=ListPullRequestsInput.model_json_schema()
        ),
        Tool(
            name="create_pull_request",
            description="""Create a new pull request.
            
            Creates a new pull request to merge changes from one branch into another.
            Can be created as a draft and allows setting maintainer permissions.
            """,
            inputSchema=CreatePullRequestInput.model_json_schema()
        ),
        Tool(
            name="update_pull_request",
            description="""Update an existing pull request.
            
            Updates pull request fields including title, body, state, base branch,
            and maintainer permissions. Only specified fields will be updated.
            """,
            inputSchema=UpdatePullRequestInput.model_json_schema()
        ),
        Tool(
            name="merge_pull_request",
            description="""Merge a pull request.
            
            Merges a pull request using the specified merge method (merge, squash, rebase).
            Can customize the merge commit title and message.
            """,
            inputSchema=MergePullRequestInput.model_json_schema()
        )
    ] 