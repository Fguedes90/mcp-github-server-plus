"""Tests for the authentication module."""

import os
import pytest
from unittest.mock import Mock, patch
from github import Github, Auth
from github.AuthenticatedUser import AuthenticatedUser
from mcp_pygithub.common.auth import (
    create_github_client,
    validate_token,
    clear_github_clients,
    GitHubClientFactory,
    DefaultGitHubClientFactory
)

# Check if we have a GitHub token for live testing
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
TEST_WITH_LIVE_API = GITHUB_TOKEN is not None

class MockGitHubClientFactory:
    """Mock implementation of GitHubClientFactory for testing."""
    
    def __init__(self, mock_client: Mock):
        self._mock_client = mock_client
        self._clients: Dict[str, Mock] = {}
    
    def create_client(self, token: str) -> Mock:
        """Return a mock client."""
        if token not in self._clients:
            self._clients[token] = self._mock_client
        return self._clients[token]
    
    def clear_cache(self) -> None:
        """Clear the mock client cache."""
        self._clients.clear()

@pytest.fixture
def mock_client():
    """Create a mock GitHub client."""
    return Mock(spec=Github)

@pytest.fixture
def mock_factory(mock_client):
    """Create a mock GitHub client factory."""
    return MockGitHubClientFactory(mock_client)

@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    user = Mock(spec=AuthenticatedUser)
    user.login = "test-user"
    return user

def test_create_github_client(mock_factory, mock_client) -> None:
    """Test creating a GitHub client using dependency injection."""
    # Test with mock token
    client = create_github_client("test-token", mock_factory)
    assert client is mock_client
    
    # Test singleton behavior - should return same instance
    client2 = create_github_client("test-token", mock_factory)
    assert client is client2
    
    # Different token should still return same mock client in test
    client3 = create_github_client("different-token", mock_factory)
    assert client is client3

def test_default_factory_behavior() -> None:
    """Test the default factory implementation."""
    # Set up mock Github class to create new client instances
    def create_mock_client(*args, **kwargs):
        return Mock(spec=Github)
    mock_github_class = Mock(side_effect=create_mock_client)
    
    # Create factory with mock Github class
    factory = DefaultGitHubClientFactory(github_class=mock_github_class)
    
    with patch('github.Auth.Token') as mock_token_class:
        # Set up mock Auth.Token instance
        mock_auth = Mock(spec=Auth.Auth)
        mock_token_class.return_value = mock_auth
        
        # Create client with test token
        client1 = factory.create_client("test-token")
        mock_token_class.assert_called_once_with("test-token")
        mock_github_class.assert_called_once_with(auth=mock_auth)
        
        # Same token should return cached client
        client2 = factory.create_client("test-token")
        assert client1 is client2
        mock_token_class.assert_called_once()
        mock_github_class.assert_called_once()
        
        # Different token should create new client
        client3 = factory.create_client("different-token")
        assert client1 is not client3
        mock_token_class.assert_called_with("different-token")
        assert mock_github_class.call_count == 2

@pytest.mark.skipif(not TEST_WITH_LIVE_API, reason="No GitHub token available")
def test_create_github_client_live() -> None:
    """Test creating a GitHub client with live token."""
    factory = DefaultGitHubClientFactory()
    client = create_github_client(GITHUB_TOKEN, factory)
    assert isinstance(client, Github)
    
    # Verify we can make API calls
    user = client.get_user()
    assert user.login is not None
    
    # Test singleton behavior with live token
    client2 = create_github_client(GITHUB_TOKEN, factory)
    assert client is client2

def test_validate_token_valid(mock_factory, mock_client, mock_user) -> None:
    """Test validating a valid token."""
    mock_client.get_user.return_value = mock_user
    
    assert validate_token("test-token", mock_factory) is True
    mock_client.get_user.assert_called_once()
    
    # Second validation attempt should reuse client
    mock_client.get_user.reset_mock()
    assert validate_token("test-token", mock_factory) is True
    mock_client.get_user.assert_called_once()

def test_validate_token_invalid(mock_factory, mock_client) -> None:
    """Test validating an invalid token."""
    mock_client.get_user.side_effect = Exception("Invalid token")
    
    assert validate_token("invalid-token", mock_factory) is False
    mock_client.get_user.assert_called_once()

@pytest.mark.skipif(not TEST_WITH_LIVE_API, reason="No GitHub token available")
def test_validate_token_live() -> None:
    """Test token validation with live token."""
    factory = DefaultGitHubClientFactory()
    
    # Test with valid token
    assert validate_token(GITHUB_TOKEN, factory) is True
    
    # Test with invalid token
    assert validate_token("invalid-token", factory) is False 