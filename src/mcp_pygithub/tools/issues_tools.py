"""Issue management tools for GitHub MCP server."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from mcp.types import Tool
from .common import (
    BaseInput, SortableInput,
    string_field, list_field
)

class ListIssuesInput(SortableInput):
    """Input schema for list_issues tool."""
    state: Optional[Literal["open", "closed", "all"]] = Field(
        default="open",
        description="State of issues to list"
    )
    labels: Optional[List[str]] = list_field(
        description="Filter by labels",
        json_schema_extra={"examples": [["bug", "high-priority"]]},
        validation_alias="labels",
        default=None
    )
    assignee: Optional[str] = string_field(
        description="Filter by assignee username",
        json_schema_extra={"examples": ["octocat"]},
        validation_alias="assignee",
        default=None
    )
    creator: Optional[str] = string_field(
        description="Filter by creator username",
        json_schema_extra={"examples": ["octocat"]},
        validation_alias="creator",
        default=None
    )
    sort: Optional[Literal["created", "updated", "comments"]] = Field(
        default="created",
        description="What to sort results by"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "state": "open",
                    "labels": ["bug", "high-priority"],
                    "assignee": "octocat",
                    "creator": "octocat",
                    "sort": "updated",
                    "direction": "desc"
                }
            ]
        }
    }

class CreateIssueInput(BaseInput):
    """Input schema for create_issue tool."""
    title: str = string_field(
        description="Issue title",
        json_schema_extra={"examples": ["Fix login bug"]},
        validation_alias="title",
        max_length=256
    )
    body: Optional[str] = string_field(
        description="Issue description in markdown",
        json_schema_extra={"examples": ["Login button not working on mobile devices"]},
        validation_alias="body",
        default=None
    )
    assignees: Optional[List[str]] = list_field(
        description="Usernames to assign issue to",
        json_schema_extra={"examples": [["octocat"]]},
        validation_alias="assignees",
        default=None
    )
    labels: Optional[List[str]] = list_field(
        description="Labels to add to issue",
        json_schema_extra={"examples": [["bug", "high-priority"]]},
        validation_alias="labels",
        default=None
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Fix login bug",
                    "body": "Login button not working on mobile devices",
                    "assignees": ["octocat"],
                    "labels": ["bug", "high-priority"]
                }
            ]
        }
    }

class UpdateIssueInput(BaseInput):
    """Input schema for update_issue tool."""
    number: int = Field(
        description="Issue number",
        validate_default=True,
        pre=True,
        json_schema_extra={"examples": [42]},
        validation_alias="number",
        strict=True,
        gt=0
    )
    title: Optional[str] = string_field(
        description="New issue title",
        json_schema_extra={"examples": ["Updated: Fix login bug"]},
        validation_alias="title",
        max_length=256,
        default=None
    )
    body: Optional[str] = string_field(
        description="New issue description in markdown",
        json_schema_extra={"examples": ["Updated description of the login bug"]},
        validation_alias="body",
        default=None
    )
    state: Optional[Literal["open", "closed"]] = Field(
        default=None,
        description="State of the issue"
    )
    assignees: Optional[List[str]] = list_field(
        description="Usernames to assign issue to",
        json_schema_extra={"examples": [["octocat", "other-dev"]]},
        validation_alias="assignees",
        default=None
    )
    labels: Optional[List[str]] = list_field(
        description="Labels for the issue",
        json_schema_extra={"examples": [["bug", "in-progress"]]},
        validation_alias="labels",
        default=None
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "number": 42,
                    "title": "Updated: Fix login bug",
                    "body": "Updated description of the login bug",
                    "state": "open",
                    "assignees": ["octocat", "other-dev"],
                    "labels": ["bug", "in-progress"]
                }
            ]
        }
    }

def issues_tools() -> List[Tool]:
    """Get issue-related tools."""
    return [
        Tool(
            name="list_issues",
            description="""List repository issues.
            
            Retrieves a list of issues. Can be filtered by state, labels,
            assignee, and creator. Supports sorting by various criteria.
            """,
            inputSchema=ListIssuesInput.model_json_schema()
        ),
        Tool(
            name="create_issue",
            description="""Create a new issue.
            
            Creates a new issue with specified title and optional body.
            Can assign users and add labels to the issue.
            """,
            inputSchema=CreateIssueInput.model_json_schema()
        ),
        Tool(
            name="update_issue",
            description="""Update an existing issue.
            
            Updates issue fields including title, body, state, assignees,
            and labels. Only specified fields will be updated.
            """,
            inputSchema=UpdateIssueInput.model_json_schema()
        )
    ] 