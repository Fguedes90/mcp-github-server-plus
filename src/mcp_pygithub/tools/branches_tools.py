"""Branch management tools for GitHub MCP server."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

from mcp.types import Tool
from .common import (
    BaseInput, SortableInput,
    string_field, list_field,
    BRANCH_NAME_PATTERN
)

class ListBranchesInput(SortableInput):
    """Input schema for list_branches tool."""
    protected: Optional[bool] = Field(
        default=None,
        description="Filter protected branches"
    )
    sort: Optional[Literal["name", "date", "committerdate", "authordate"]] = Field(
        default="name",
        description="Sort branches by"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "protected": True,
                    "sort": "date",
                    "direction": "desc"
                }
            ]
        }
    }

class CreateBranchInput(BaseInput):
    """Input schema for create_branch tool."""
    name: str = string_field(
        description="New branch name",
        json_schema_extra={"examples": ["feature/new-login"]},
        validation_alias="name",
        pattern=BRANCH_NAME_PATTERN
    )
    source: str = string_field(
        description="Source branch or commit SHA",
        json_schema_extra={"examples": ["main"]},
        validation_alias="source"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "feature/new-login",
                    "source": "main"
                }
            ]
        }
    }

class UpdateBranchProtectionInput(BaseInput):
    """Input schema for update_branch_protection tool."""
    branch: str = string_field(
        description="Branch name to protect",
        json_schema_extra={"examples": ["main"]},
        validation_alias="branch"
    )
    required_status_checks: Optional[List[str]] = list_field(
        description="Required status check contexts",
        json_schema_extra={"examples": [["ci/build", "ci/test"]]},
        validation_alias="required_status_checks",
        default=None
    )
    enforce_admins: Optional[bool] = Field(
        default=True,
        description="Enforce protections for admins"
    )
    required_pull_request_reviews: Optional[bool] = Field(
        default=True,
        description="Require pull request reviews"
    )
    required_approving_review_count: Optional[int] = Field(
        default=1,
        description="Number of required approving reviews",
        validate_default=True,
        pre=True,
        json_schema_extra={"examples": [2]},
        validation_alias="required_approving_review_count",
        strict=True,
        ge=1,
        le=6
    )
    dismiss_stale_reviews: Optional[bool] = Field(
        default=True,
        description="Dismiss stale pull request approvals"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "branch": "main",
                    "required_status_checks": ["ci/build", "ci/test"],
                    "enforce_admins": True,
                    "required_pull_request_reviews": True,
                    "required_approving_review_count": 2,
                    "dismiss_stale_reviews": True
                }
            ]
        }
    }

class DeleteBranchInput(BaseInput):
    """Input schema for delete_branch tool."""
    name: str = string_field(
        description="Branch name to delete",
        json_schema_extra={"examples": ["feature/old-feature"]},
        validation_alias="name",
        pattern=r"^(?:feature/|bugfix/|release/|hotfix/|develop).*$"  # Deve ser um branch de feature, bugfix, release, hotfix ou develop
    )

    @field_validator("name")
    @classmethod
    def validate_branch_name(cls, v: str) -> str:
        """Validate branch name is not main or master."""
        if v in ["main", "master"]:
            raise ValueError("Cannot delete main or master branch")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "feature/old-feature"
                }
            ]
        }
    }

def branches_tools() -> List[Tool]:
    """Get branch-related tools."""
    return [
        Tool(
            name="list_branches",
            description="""List repository branches.
            
            Retrieves a list of branches from the repository. Can be filtered by
            protection status and sorted by various criteria.
            """,
            inputSchema=ListBranchesInput.model_json_schema()
        ),
        Tool(
            name="create_branch",
            description="""Create a new branch.
            
            Creates a new branch from a specified source (branch name or commit SHA).
            Branch names must follow naming conventions (feature/, bugfix/, etc.).
            """,
            inputSchema=CreateBranchInput.model_json_schema()
        ),
        Tool(
            name="update_branch_protection",
            description="""Update branch protection rules.
            
            Configures protection rules for a branch including required status checks,
            pull request reviews, and admin enforcement.
            """,
            inputSchema=UpdateBranchProtectionInput.model_json_schema()
        ),
        Tool(
            name="delete_branch",
            description="""Delete a branch.
            
            Permanently deletes a branch. Cannot delete main/master branches.
            This action cannot be undone.
            """,
            inputSchema=DeleteBranchInput.model_json_schema()
        )
    ] 