"""Search tools for GitHub MCP server."""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.functional_validators import BeforeValidator

from mcp.types import Tool

def validate_non_empty_str(v: str) -> str:
    """Validate string is non-empty."""
    if not v or not isinstance(v, str):
        raise ValueError("Must be a non-empty string")
    return v

def validate_relative_path(v: Optional[str]) -> Optional[str]:
    """Validate path is relative."""
    if v is not None:
        if not isinstance(v, str):
            raise ValueError("Path must be a string")
        if v.startswith('/'):
            raise ValueError("Path must be relative (no leading slash)")
    return v

def validate_extension(v: Optional[str]) -> Optional[str]:
    """Validate and normalize file extension."""
    if v is not None:
        if not isinstance(v, str):
            raise ValueError("Extension must be a string")
        if not v.startswith('.'):
            v = '.' + v
    return v

def validate_labels(v: Optional[List[str]]) -> Optional[List[str]]:
    """Validate list of label strings."""
    if v is not None:
        if not isinstance(v, list):
            raise ValueError("Labels must be a list of strings")
        if not all(isinstance(label, str) for label in v):
            raise ValueError("All labels must be strings")
    return v

def validate_iso_date(v: Optional[str]) -> Optional[str]:
    """Validate ISO 8601 date string."""
    if v is not None:
        if not isinstance(v, str):
            raise ValueError("Date must be a string")
        if not v.startswith(('2', '1')) or len(v) < 10:
            raise ValueError("Date must be in ISO 8601 format (YYYY-MM-DD...)")
    return v

class SearchCodeInput(BaseModel):
    """Input schema for search_code tool."""
    query: str = Field(
        description="Search query string",
        validate_default=True,
        pre=True,
        json_schema_extra={"examples": ["TODO:"]},
        validation_alias="query",
        strict=True,
        min_length=1
    )
    path: Optional[str] = Field(
        default=None,
        description="Limit search to files under this path",
        pre=True,
        json_schema_extra={"examples": ["src"]},
        validate_default=True,
        validation_alias="path",
        strict=True,
        pattern=r"^[^/].*$",  # Não pode começar com /
    )
    extension: Optional[str] = Field(
        default=None,
        description="Limit search to files with this extension",
        pre=True,
        json_schema_extra={"examples": [".py"]},
        validate_default=True,
        validation_alias="extension",
        strict=True,
        pattern=r"^\.?[a-zA-Z0-9]+$"  # Deve ser uma extensão válida
    )
    case_sensitive: Optional[bool] = Field(
        default=False,
        description="Whether to perform case-sensitive search"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "TODO:",
                    "path": "src",
                    "extension": ".py",
                    "case_sensitive": False
                }
            ]
        }
    }

class SearchIssuesInput(BaseModel):
    """Input schema for search_issues tool."""
    query: str = Field(
        description="Search query string",
        validate_default=True,
        pre=True,
        json_schema_extra={"examples": ["bug login"]},
        validation_alias="query",
        strict=True,
        min_length=1
    )
    state: Optional[Literal["open", "closed", "all"]] = Field(
        default="open",
        description="State of issues to search"
    )
    labels: Optional[List[str]] = Field(
        default=None,
        description="Filter by labels",
        pre=True,
        validate_default=True,
        validation_alias="labels",
        strict=True,
        min_items=1,
        item_type=str
    )
    sort: Optional[Literal["created", "updated", "comments"]] = Field(
        default="created",
        description="What to sort results by"
    )
    direction: Optional[Literal["asc", "desc"]] = Field(
        default="desc",
        description="Direction of sort"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "bug login",
                    "state": "open",
                    "labels": ["bug", "high-priority"],
                    "sort": "updated",
                    "direction": "desc"
                }
            ]
        }
    }

class SearchCommitsInput(BaseModel):
    """Input schema for search_commits tool."""
    query: str = Field(
        description="Search query string",
        validate_default=True,
        pre=True,
        json_schema_extra={"examples": ["fix bug"]},
        validation_alias="query",
        strict=True,
        min_length=1
    )
    author: Optional[str] = Field(
        default=None,
        description="Filter by commit author",
        pre=True,
        validate_default=True,
        validation_alias="author",
        strict=True,
        min_length=1
    )
    since: Optional[str] = Field(
        default=None,
        description="Filter commits after this date (ISO 8601 format)",
        pre=True,
        validate_default=True,
        validation_alias="since",
        strict=True,
        pattern=r"^\d{4}-\d{2}-\d{2}"  # Formato ISO 8601 básico
    )
    until: Optional[str] = Field(
        default=None,
        description="Filter commits before this date (ISO 8601 format)",
        pre=True,
        validate_default=True,
        validation_alias="until",
        strict=True,
        pattern=r"^\d{4}-\d{2}-\d{2}"  # Formato ISO 8601 básico
    )
    path: Optional[str] = Field(
        default=None,
        description="Filter commits modifying this path",
        pre=True,
        validate_default=True,
        validation_alias="path",
        strict=True,
        pattern=r"^[^/].*$"  # Não pode começar com /
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "fix bug",
                    "author": "octocat",
                    "since": "2024-01-01",
                    "until": "2024-03-31",
                    "path": "src/main.py"
                }
            ]
        }
    }

def search_tools() -> List[Tool]:
    """Get search-related tools."""
    return [
        Tool(
            name="search_code",
            description="""Search for code in the repository.
            
            Searches for code matching the query string. Can be limited to specific
            paths or file extensions, and supports case-sensitive search.
            """,
            inputSchema=SearchCodeInput.model_json_schema()
        ),
        Tool(
            name="search_issues",
            description="""Search for issues in the repository.
            
            Searches for issues matching the query string. Can be filtered by state,
            labels, and supports sorting by various criteria.
            """,
            inputSchema=SearchIssuesInput.model_json_schema()
        ),
        Tool(
            name="search_commits",
            description="""Search for commits in the repository.
            
            Searches for commits matching the query string. Can be filtered by author,
            date range, and files modified.
            """,
            inputSchema=SearchCommitsInput.model_json_schema()
        )
    ] 