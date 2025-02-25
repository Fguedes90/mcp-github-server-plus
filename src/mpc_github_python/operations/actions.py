"""Actions module for GitHub workflow operations."""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from pydantic import BaseModel
from github.Repository import Repository as GithubRepository
from github.Workflow import Workflow
from github.WorkflowRun import WorkflowRun
from github.GithubObject import NotSet

class WorkflowConfig(BaseModel):
    """Configuration for workflow operations."""
    name: str
    event: str
    ref: Optional[str] = None
    inputs: Optional[Dict[str, str]] = None

class WorkflowRunConfig(BaseModel):
    """Configuration for workflow run operations."""
    run_id: Union[str, int]

class ActionManager:
    """Manages GitHub workflow operations."""
    
    def __init__(self, repository: GithubRepository) -> None:
        """Initialize the action manager.
        
        Args:
            repository: GitHub repository to operate on
        """
        self.repository = repository
    
    async def get_workflow(self, workflow_id: int) -> Workflow:
        """Get a workflow by ID.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            The workflow
        """
        return self.repository.get_workflow(workflow_id)
    
    async def list_workflows(self) -> List[Workflow]:
        """List all workflows in the repository.
        
        Returns:
            List of workflows
        """
        return list(self.repository.get_workflows())
    
    async def list_workflow_runs(
        self,
        workflow: Optional[Workflow] = None,
    ) -> List[WorkflowRun]:
        """List workflow runs.
        
        Args:
            workflow: Optional workflow to list runs for
            
        Returns:
            List of workflow runs
        """
        if workflow:
            return list(workflow.get_runs())
        return list(self.repository.get_workflow_runs())
    
    async def create_workflow_dispatch(
        self,
        workflow: Workflow,
        config: WorkflowConfig,
    ) -> Optional[WorkflowRun]:
        """Create a workflow dispatch event.
        
        Args:
            workflow: Workflow to dispatch
            config: Workflow configuration
            
        Returns:
            The workflow run if available
        """
        # Validate config
        config = WorkflowConfig.model_validate(config)
        
        ref = config.ref or self.repository.default_branch
        inputs = config.inputs or NotSet
        
        workflow.create_dispatch(
            ref=ref,
            inputs=inputs,
        )
        
        # Get the latest run
        runs = list(workflow.get_runs())
        return runs[0] if runs else None
    
    async def cancel_workflow_run(self, run: WorkflowRun) -> None:
        """Cancel a workflow run.
        
        Args:
            run: Workflow run to cancel
        """
        run.cancel()
    
    async def rerun_workflow_run(self, run: WorkflowRun) -> None:
        """Rerun a workflow run.
        
        Args:
            run: Workflow run to rerun
        """
        run.rerun()
    
    async def debug_workflow_run(
        self,
        config: WorkflowRunConfig,
    ) -> Dict[str, str]:
        """Debug a workflow run by getting its logs URL.
        
        Args:
            config: Workflow run configuration
            
        Returns:
            Dictionary containing the logs URL
        """
        # Validate config
        config = WorkflowRunConfig.model_validate(config)
        
        run = self.repository.get_workflow_run(config.run_id)
        if not run:
            raise ValueError(f"No workflow run found with ID {config.run_id}")
        
        logs_url = run.logs_url
        if not logs_url:
            raise ValueError("No logs found for this workflow run")
        
        return {"logs_url": logs_url} 