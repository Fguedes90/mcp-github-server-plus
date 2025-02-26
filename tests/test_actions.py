"""Tests for the actions module."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any
from github.GithubObject import NotSet
from github.Repository import Repository
from github.Workflow import Workflow
from github.WorkflowRun import WorkflowRun
import github.Auth

from mcp_pygithub.operations.actions import ActionManager
from mcp_pygithub.server.handlers import GitHubHandler
from mcp_pygithub.common.auth import GitHubClientFactory
from mcp_pygithub.common.errors import NotFoundError, GitHubError
from mcp_pygithub.tools.actions_tools import (
    ListWorkflowsInput,
    GetWorkflowRunsInput,
    TriggerWorkflowInput,
    CancelWorkflowRunInput,
    GetWorkflowRunLogsInput
)

class MockGitHubClientFactory(GitHubClientFactory):
    """Mock factory for testing."""
    def __init__(self, mock_client: MagicMock):
        self._mock_client = mock_client
        self._clients: Dict[str, MagicMock] = {}
    
    def create_client(self, token: str) -> MagicMock:
        """Return a mock client."""
        if token not in self._clients:
            self._clients[token] = self._mock_client
        return self._clients[token]
    
    def clear_cache(self) -> None:
        """Clear the mock client cache."""
        self._clients.clear()

@pytest.fixture
def mock_workflow_runs(mock_workflow_run: MagicMock) -> MagicMock:
    """Mock workflow runs list with filter methods."""
    runs = MagicMock()
    runs.__iter__.return_value = [mock_workflow_run]
    runs.get_branch.return_value = runs
    runs.get_event.return_value = runs 
    runs.get_status.return_value = runs
    return runs

@pytest.fixture
def mock_workflow(mock_workflow_runs: MagicMock) -> MagicMock:
    """Mock GitHub workflow."""
    workflow = MagicMock(spec=Workflow)
    workflow.get_runs.return_value = mock_workflow_runs
    workflow.id = 123
    workflow.path = "test.yml"
    workflow.state = "active"
    return workflow

@pytest.fixture
def mock_workflow_run() -> MagicMock:
    """Create a mock workflow run."""
    run = MagicMock(spec=WorkflowRun)
    run.id = 456
    run.status = "completed"
    run.download_logs = MagicMock(return_value=b"test logs")
    run.cancel = MagicMock(return_value=True)
    return run

@pytest.fixture
def mock_repository(mock_workflow: MagicMock, mock_workflow_run: MagicMock) -> MagicMock:
    """Create a mock repository."""
    repo = MagicMock()
    repo.get_workflow.return_value = mock_workflow
    repo.get_workflows.return_value = [mock_workflow]
    repo.get_workflow_run.return_value = mock_workflow_run
    repo.get_workflow_runs.return_value = mock_workflow_runs
    return repo

@pytest.fixture
def mock_github(mock_repository: MagicMock) -> MagicMock:
    """Create a mock GitHub client."""
    github = MagicMock()
    github.get_repo.return_value = mock_repository
    return github

@pytest.fixture
def mock_auth() -> MagicMock:
    """Create a mock auth object."""
    auth = MagicMock(spec=github.Auth.Auth)
    return auth

@pytest.fixture
def mock_github_class(mock_auth: MagicMock) -> MagicMock:
    """Create a mock GitHub class."""
    github_class = MagicMock()
    github_class.return_value = mock_github
    return github_class

@pytest.fixture
def mock_factory(mock_github: MagicMock) -> MagicMock:
    """Create a mock factory."""
    factory = MagicMock()
    factory.create_client.return_value = mock_github
    return factory

@pytest.fixture
def action_manager(mock_repository: MagicMock, mock_factory: MagicMock) -> ActionManager:
    """Create an action manager for testing."""
    return ActionManager(mock_repository, mock_factory)

@pytest_asyncio.fixture
async def handler(mock_repository: MagicMock) -> GitHubHandler:
    """Create a GitHub handler for testing."""
    handler = GitHubHandler("test_token")
    await handler.initialize()
    handler._repository = mock_repository
    handler._actions = ActionManager(mock_repository)
    handler._initialized = True
    return handler

# Tests for ActionManager

@pytest.mark.asyncio
async def test_get_workflow_by_id(action_manager: ActionManager, mock_repository: MagicMock, mock_workflow: MagicMock) -> None:
    """Test getting a workflow by numeric ID."""
    mock_repository.get_workflow.return_value = mock_workflow
    workflow = await action_manager.get_workflow("123")
    assert workflow == mock_workflow
    mock_repository.get_workflow.assert_called_once_with(123)

@pytest.mark.asyncio
async def test_get_workflow_by_filename(action_manager: ActionManager, mock_repository: MagicMock, mock_workflow: MagicMock) -> None:
    """Test getting a workflow by filename."""
    mock_repository.get_workflows.return_value = [mock_workflow]
    workflow = await action_manager.get_workflow("test.yml")
    assert workflow == mock_workflow
    mock_repository.get_workflows.assert_called_once()

@pytest.mark.asyncio
async def test_get_workflow_not_found(action_manager: ActionManager, mock_repository: MagicMock) -> None:
    """Test getting a non-existent workflow."""
    mock_repository.get_workflow.side_effect = Exception("Not Found")
    with pytest.raises(NotFoundError):
        await action_manager.get_workflow("999")

@pytest.mark.asyncio
async def test_list_workflows(action_manager: ActionManager, mock_repository: MagicMock, mock_workflow: MagicMock) -> None:
    """Test listing all workflows."""
    mock_repository.get_workflows.return_value = [mock_workflow]
    workflows = await action_manager.list_workflows()
    assert workflows == [mock_workflow]
    mock_repository.get_workflows.assert_called_once()

@pytest.mark.asyncio
async def test_list_workflows_with_state(action_manager: ActionManager, mock_repository: MagicMock, mock_workflow: MagicMock) -> None:
    """Test listing workflows filtered by state."""
    mock_repository.get_workflows.return_value = [mock_workflow]
    workflows = await action_manager.list_workflows(state="active")
    assert workflows == [mock_workflow]
    mock_repository.get_workflows.assert_called_once()

@pytest.mark.asyncio
async def test_get_workflow_run(action_manager: ActionManager, mock_repository: MagicMock, mock_workflow_run: MagicMock) -> None:
    """Test getting a workflow run by ID."""
    mock_repository.get_workflow_run.return_value = mock_workflow_run
    run = await action_manager.get_workflow_run(456)
    assert run == mock_workflow_run
    mock_repository.get_workflow_run.assert_called_once_with(456)

@pytest.mark.asyncio
async def test_list_workflow_runs_no_filters(action_manager: ActionManager, mock_repository: MagicMock, mock_workflow_run: MagicMock) -> None:
    """Test listing workflow runs without filters."""
    mock_repository.get_workflow_runs.return_value = [mock_workflow_run]
    runs = await action_manager.list_workflow_runs()
    assert runs == [mock_workflow_run]
    mock_repository.get_workflow_runs.assert_called_once()

@pytest.mark.asyncio
async def test_list_workflow_runs_with_workflow(action_manager: ActionManager, mock_repository: MagicMock, mock_workflow: MagicMock, mock_workflow_run: MagicMock) -> None:
    """Test listing workflow runs for a specific workflow."""
    mock_repository.get_workflow.return_value = mock_workflow
    mock_workflow.get_runs.return_value = [mock_workflow_run]
    runs = await action_manager.list_workflow_runs(workflow_id="123")
    assert runs == [mock_workflow_run]
    mock_repository.get_workflow.assert_called_once_with(123)
    mock_workflow.get_runs.assert_called_once()

@pytest.mark.asyncio
async def test_list_workflow_runs_with_filters(action_manager: ActionManager, mock_repository: MagicMock, mock_workflow_run: MagicMock) -> None:
    """Test listing workflow runs with filters."""
    runs_paginated = MagicMock()
    runs_paginated.get_branch.return_value = runs_paginated
    runs_paginated.get_event.return_value = runs_paginated
    runs_paginated.get_status.return_value = [mock_workflow_run]
    mock_repository.get_workflow_runs.return_value = runs_paginated
    
    runs = await action_manager.list_workflow_runs(
        branch="feature",
        event="push",
        status="completed"
    )
    
    assert runs == [mock_workflow_run]
    runs_paginated.get_branch.assert_called_once_with("feature")
    runs_paginated.get_event.assert_called_once_with("push")
    runs_paginated.get_status.assert_called_once_with("completed")

@pytest.mark.asyncio
async def test_trigger_workflow(action_manager: ActionManager, mock_repository: MagicMock, mock_workflow: MagicMock) -> None:
    """Test triggering a workflow."""
    mock_repository.get_workflows.return_value = [mock_workflow]
    mock_workflow.create_dispatch.return_value = True
    
    result = await action_manager.trigger_workflow(
        workflow_id="test.yml",
        ref="main",
        inputs={"env": "prod"}
    )
    
    assert result is True
    mock_repository.get_workflows.assert_called_once()
    mock_workflow.create_dispatch.assert_called_once_with("main", {"env": "prod"})

@pytest.mark.asyncio
async def test_cancel_workflow_run(action_manager: ActionManager, mock_repository: MagicMock, mock_workflow_run: MagicMock) -> None:
    """Test cancelling a workflow run."""
    mock_repository.get_workflow_run.return_value = mock_workflow_run
    mock_workflow_run.cancel.return_value = True
    result = await action_manager.cancel_workflow_run(456)
    assert result is True
    mock_repository.get_workflow_run.assert_called_once_with(456)
    mock_workflow_run.cancel.assert_called_once()

@pytest.mark.asyncio
async def test_get_workflow_run_logs(action_manager: ActionManager, mock_repository: MagicMock, mock_workflow_run: MagicMock) -> None:
    """Test getting workflow run logs."""
    mock_repository.get_workflow_run.return_value = mock_workflow_run
    logs = await action_manager.get_workflow_run_logs(456)
    assert logs == b"test logs"
    mock_repository.get_workflow_run.assert_called_once_with(456)
    mock_workflow_run.download_logs.assert_called_once()

# Tests for Handler

@pytest.mark.asyncio
async def test_handler_list_workflows(handler: GitHubHandler, mock_repository: MagicMock, mock_workflow: MagicMock) -> None:
    """Test handler list_workflows tool."""
    mock_repository.get_workflows.return_value = [mock_workflow]
    result = await handler.call_tool("list_workflows", {"state": "active"})
    assert result == [mock_workflow]

@pytest.mark.asyncio
async def test_handler_get_workflow_runs(handler: GitHubHandler, mock_repository: MagicMock, mock_workflow: MagicMock, mock_workflow_run: MagicMock) -> None:
    """Test handler get_workflow_runs tool."""
    # Create a mock for workflow runs with filter methods
    runs = MagicMock()
    runs.__iter__.return_value = [mock_workflow_run]
    runs.get_branch.return_value = runs
    runs.get_event.return_value = runs
    runs.get_status.return_value = runs

    # Set up the mock workflow
    mock_workflow.get_runs.return_value = runs

    # Set up the mock repository
    mock_repository.get_workflow.return_value = mock_workflow
    mock_repository.get_workflows.return_value = [mock_workflow]
    
    # Set the mock repository in the handler's action manager
    handler._actions._repository = mock_repository

    result = await handler.call_tool("get_workflow_runs", {
        "workflow_id": "test.yml",
        "branch": "main",
        "status": "completed"
    })

    assert result == [mock_workflow_run]
    mock_repository.get_workflows.assert_called_once()

@pytest.mark.asyncio
async def test_handler_trigger_workflow(handler: GitHubHandler, mock_repository: MagicMock, mock_workflow: MagicMock) -> None:
    """Test handler trigger_workflow tool."""
    mock_repository.get_workflow.return_value = mock_workflow
    mock_workflow.create_dispatch.return_value = True
    result = await handler.call_tool("trigger_workflow", {
        "workflow_id": "test.yml",
        "ref": "main",
        "inputs": {"env": "prod"}
    })
    assert result is True

@pytest.mark.asyncio
async def test_handler_cancel_workflow_run(handler: GitHubHandler, mock_repository: MagicMock, mock_workflow_run: MagicMock) -> None:
    """Test handler cancel_workflow_run tool."""
    mock_repository.get_workflow_run.return_value = mock_workflow_run
    result = await handler.call_tool("cancel_workflow_run", {
        "run_id": 456
    })
    assert result is True
    mock_workflow_run.cancel.assert_called_once()

@pytest.mark.asyncio
async def test_handler_get_workflow_run_logs(handler: GitHubHandler, mock_repository: MagicMock, mock_workflow_run: MagicMock) -> None:
    """Test handler get_workflow_run_logs tool."""
    mock_repository.get_workflow_run.return_value = mock_workflow_run
    result = await handler.call_tool("get_workflow_run_logs", {"run_id": 456})
    assert result == b"test logs"

@pytest.mark.asyncio
async def test_handler_invalid_tool(handler: GitHubHandler) -> None:
    """Test handler with invalid tool name."""
    with pytest.raises(ValueError, match="Tool invalid_tool not found"):
        await handler.call_tool("invalid_tool", {}) 