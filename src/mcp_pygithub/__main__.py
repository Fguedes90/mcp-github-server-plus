"""MCP server application for GitHub Python."""

import os
from typing import Optional, Any, List, Dict

from fastmcp import FastMCP, Context
from mcp_pygithub.common.version import __version__
from mcp_pygithub.operations import ActionManager, RepositoryManager
from mcp_pygithub.operations.repository import RepositoryConfig

# Create FastMCP instance
mcp = FastMCP(
    "GitHub Tools",
    version=__version__,
    description="MCP server for GitHub workflow operations",
)

async def get_action_manager() -> ActionManager:
    """Get a new action manager instance."""
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        raise ValueError("GITHUB_PERSONAL_ACCESS_TOKEN environment variable is required")
        
    repository_config = RepositoryConfig(
        token=token,
        name="mcp-github-server-plus",
        owner="Fguedes90"
    )
    repository_manager = RepositoryManager(repository_config)
    repository = await repository_manager.get_repository()
    return ActionManager(repository)

@mcp.tool()
async def list_workflows() -> List[Dict[str, Any]]:
    """List all workflows in the repository."""
    action_manager = await get_action_manager()
    return await action_manager.list_workflows({})

@mcp.tool()
async def get_workflow_runs(workflow_id: str) -> List[Dict[str, Any]]:
    """Get runs for a specific workflow."""
    action_manager = await get_action_manager()
    return await action_manager.list_workflow_runs({"workflow_id": workflow_id})

@mcp.tool()
async def trigger_workflow(workflow_id: str, ref: str = "main") -> Dict[str, Any]:
    """Trigger a workflow run."""
    action_manager = await get_action_manager()
    return await action_manager.trigger_workflow({
        "workflow_id": workflow_id,
        "ref": ref
    })

@mcp.tool()
async def cancel_workflow_run(run_id: str) -> Dict[str, Any]:
    """Cancel a workflow run."""
    action_manager = await get_action_manager()
    return await action_manager.cancel_workflow_run({"run_id": run_id})

@mcp.tool()
async def get_workflow_run_logs(run_id: str) -> str:
    """Get logs for a workflow run."""
    action_manager = await get_action_manager()
    return await action_manager.get_workflow_run_logs({"run_id": run_id})

def main() -> None:
    """Entry point for the FastMCP server application."""
    if os.getenv("DEBUG", "false").lower() == "true":
        mcp.debug = True
    
    print("FastMCP server is running...")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()