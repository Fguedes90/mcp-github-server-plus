"""GitHub Actions tools for GitHub MCP server."""

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from ..common.utils import validate_branch_name, sanitize_ref_name

from mcp.types import Tool
from .common import BaseInput, string_field

class WorkflowInput(BaseInput):
    """Base input schema for workflow operations."""
    workflow_id: str = string_field(
        description="Workflow ID or file name",
        json_schema_extra={"examples": ["ci.yml"]},
    )

    @field_validator("workflow_id")
    @classmethod
    def validate_workflow_id(cls, v: str) -> str:
        """Validate workflow ID can be numeric or a valid filename."""
        if v.isdigit() or v.endswith('.yml') or v.endswith('.yaml'):
            return v
        raise ValueError("Workflow ID must be numeric or end with .yml/.yaml")

class WorkflowRunInput(WorkflowInput):
    """Base input schema for workflow run operations."""
    run_id: int = Field(
        ...,
        description="Workflow run ID",
        gt=0,
        json_schema_extra={"examples": [12345]}
    )

class ListWorkflowsInput(BaseInput):
    """Input schema for list_workflows tool."""
    state: Optional[Literal["active", "deleted", "disabled_fork", "disabled_inactivity", "disabled_manually"]] = Field(
        default="active",
        description="Filter workflows by state"
    )

class GetWorkflowRunsInput(WorkflowInput):
    """Input schema for get_workflow_runs tool."""
    status: Optional[Literal[
        "completed", "action_required", "cancelled", "failure", 
        "neutral", "skipped", "stale", "success", "timed_out", 
        "in_progress", "queued", "requested", "waiting"
    ]] = None
    branch: Optional[str] = string_field(
        description="Filter runs by branch",
        default=None
    )
    event: Optional[str] = string_field(
        description="Filter runs by event type",
        pattern=r"^(push|pull_request|schedule|workflow_dispatch|repository_dispatch|release|deployment)$",
        default=None
    )

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v: Optional[str]) -> Optional[str]:
        """Validate branch name if provided."""
        if v is not None and not validate_branch_name(v):
            raise ValueError(f"Invalid branch name: {v}")
        return v

class TriggerWorkflowInput(WorkflowInput):
    """Input schema for trigger_workflow tool."""
    ref: str = string_field(
        description="Git reference (branch/tag) to run workflow on"
    )
    inputs: Optional[Dict[str, str]] = Field(
        default=None,
        description="Input parameters for workflow"
    )

    @field_validator("ref")
    @classmethod
    def validate_ref(cls, v: str) -> str:
        """Validate Git reference name."""
        try:
            return sanitize_ref_name(v)
        except ValueError as e:
            raise ValueError(f"Invalid Git reference name: {v}") from e

    @field_validator("inputs")
    @classmethod
    def validate_inputs(cls, v: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Validate workflow inputs if provided."""
        if v is not None:
            # Validate input values are strings
            for key, value in v.items():
                if not isinstance(value, str):
                    raise ValueError(f"Input value for '{key}' must be a string")
        return v

class CancelWorkflowRunInput(BaseModel):
    """Input for canceling a workflow run."""

    run_id: int = Field(description="ID of the workflow run to cancel")

class GetWorkflowRunLogsInput(BaseInput):
    """Input schema for get_workflow_run_logs tool."""
    run_id: int = Field(
        ...,
        description="Workflow run ID to get logs from",
        gt=0,
        json_schema_extra={"examples": [12345]}
    )

def actions_tools() -> List[Tool]:
    """Get GitHub Actions-related tools."""
    return [
        Tool(
            name="list_workflows",
            description="List repository workflows filtered by state.",
            inputSchema=ListWorkflowsInput.model_json_schema()
        ),
        Tool(
            name="get_workflow_runs",
            description="Get workflow runs filtered by status, branch, and event type.",
            inputSchema=GetWorkflowRunsInput.model_json_schema()
        ),
        Tool(
            name="trigger_workflow",
            description="Manually trigger a workflow run on a specific Git reference with optional inputs.",
            inputSchema=TriggerWorkflowInput.model_json_schema()
        ),
        Tool(
            name="cancel_workflow_run", 
            description="Cancel a running workflow by its run ID.",
            inputSchema=CancelWorkflowRunInput.model_json_schema()
        ),
        Tool(
            name="get_workflow_run_logs",
            description="Get the logs from a workflow run.",
            inputSchema=GetWorkflowRunLogsInput.model_json_schema()
        )
    ] 