"""Module for managing GitHub Actions workflows."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from github.Repository import Repository as GithubRepository
from github.Workflow import Workflow
from github.WorkflowRun import WorkflowRun
from github.GithubObject import NotSet

from ..common.errors import (
    NotFoundError,
    GitHubError
)
from ..common.auth import GitHubClientFactory, DefaultGitHubClientFactory

@dataclass
class ActionConfig:
    """Configuration for workflow operations."""
    workflow_id: Optional[int] = None
    run_id: Optional[int] = None
    branch: Optional[str] = None
    event: Optional[str] = None
    status: Optional[str] = None
    conclusion: Optional[str] = None

class ActionManager:
    """Manager for GitHub Actions workflow operations."""

    def __init__(self, repository: GithubRepository, factory: Optional[GitHubClientFactory] = None) -> None:
        """Initialize the action manager.
        
        Args:
            repository: The GitHub repository to manage workflows for.
            factory: Optional GitHub client factory for authentication.
        """
        self._repository = repository
        self._factory = factory or DefaultGitHubClientFactory()

    async def get_workflow(self, workflow_id: str) -> Workflow:
        """Get a workflow by ID or filename.
        
        Args:
            workflow_id: The workflow ID or filename.
            
        Returns:
            The GitHub workflow.
            
        Raises:
            NotFoundError: If the workflow is not found.
            GitHubError: If there is an error getting the workflow.
        """
        try:
            # Try as numeric ID first
            if workflow_id.isdigit():
                return self._repository.get_workflow(int(workflow_id))
            # Try as filename
            workflows = self._repository.get_workflows()
            for workflow in workflows:
                if workflow.path.endswith(workflow_id):
                    return workflow
            raise NotFoundError(f"Workflow not found: {workflow_id}")
        except Exception as e:
            if "Not Found" in str(e):
                raise NotFoundError(f"Workflow not found: {workflow_id}") from e
            raise GitHubError(f"Error getting workflow: {e}") from e

    async def list_workflows(self, state: Optional[str] = None) -> List[Workflow]:
        """List all workflows in the repository.
        
        Args:
            state: Optional state to filter by.
            
        Returns:
            List of GitHub workflows.
            
        Raises:
            GitHubError: If there is an error listing workflows.
        """
        try:
            workflows = list(self._repository.get_workflows())
            if state:
                workflows = [w for w in workflows if w.state == state]
            return workflows
        except Exception as e:
            raise GitHubError(f"Error listing workflows: {e}") from e

    async def get_workflow_run(self, run_id: int) -> WorkflowRun:
        """Get a workflow run by ID.
        
        Args:
            run_id: The workflow run ID.
            
        Returns:
            The GitHub workflow run.
            
        Raises:
            NotFoundError: If the workflow run is not found.
            GitHubError: If there is an error getting the run.
        """
        try:
            return self._repository.get_workflow_run(run_id)
        except Exception as e:
            if "Not Found" in str(e):
                raise NotFoundError(f"Workflow run not found: {run_id}") from e
            raise GitHubError(f"Error getting workflow run: {e}") from e

    async def list_workflow_runs(
        self,
        workflow_id: Optional[str] = None,
        branch: Optional[str] = None,
        event: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[WorkflowRun]:
        """List workflow runs with optional filters.
        
        Args:
            workflow_id: Optional workflow ID or filename to filter by.
            branch: Optional branch name to filter by.
            event: Optional event type to filter by.
            status: Optional status to filter by.
            
        Returns:
            List of GitHub workflow runs.
            
        Raises:
            GitHubError: If there is an error listing runs.
        """
        try:
            # Get runs from workflow or repository
            if workflow_id:
                workflow = await self.get_workflow(workflow_id)
                runs = workflow.get_runs()
            else:
                runs = self._repository.get_workflow_runs()

            # Apply filters
            branch = branch if branch is not None else NotSet
            event = event if event is not None else NotSet
            status = status if status is not None else NotSet

            filtered_runs = runs
            if branch is not NotSet:
                filtered_runs = filtered_runs.get_branch(branch)
            if event is not NotSet:
                filtered_runs = filtered_runs.get_event(event)
            if status is not NotSet:
                filtered_runs = filtered_runs.get_status(status)

            return list(filtered_runs)
        except Exception as e:
            raise GitHubError(f"Error listing workflow runs: {e}") from e

    async def trigger_workflow(
        self,
        workflow_id: str,
        ref: str,
        inputs: Optional[Dict[str, Any]] = None
    ) -> WorkflowRun:
        """Trigger a workflow run.
        
        Args:
            workflow_id: The workflow ID or filename.
            ref: The Git reference to run on.
            inputs: Optional input parameters.
            
        Returns:
            The created workflow run.
            
        Raises:
            NotFoundError: If the workflow is not found.
            GitHubError: If there is an error triggering the workflow.
        """
        try:
            workflow = await self.get_workflow(workflow_id)
            return workflow.create_dispatch(ref, inputs or {})
        except Exception as e:
            raise GitHubError(f"Error triggering workflow: {e}") from e

    async def cancel_workflow_run(self, run_id: int) -> bool:
        """Cancel a workflow run.
        
        Args:
            run_id: The workflow run ID.
            
        Returns:
            True if cancelled successfully.
            
        Raises:
            NotFoundError: If the workflow run is not found.
            GitHubError: If there is an error cancelling the run.
        """
        try:
            run = await self.get_workflow_run(run_id)
            return run.cancel()
        except Exception as e:
            raise GitHubError(f"Error cancelling workflow run: {e}") from e

    async def get_workflow_run_logs(self, run_id: int) -> bytes:
        """Get the logs for a workflow run.
        
        Args:
            run_id: The workflow run ID.
            
        Returns:
            The workflow run logs.
            
        Raises:
            NotFoundError: If the workflow run is not found.
            GitHubError: If there is an error getting the logs.
        """
        try:
            run = await self.get_workflow_run(run_id)
            return run.download_logs()
        except Exception as e:
            raise GitHubError(f"Error getting workflow run logs: {e}") from e 